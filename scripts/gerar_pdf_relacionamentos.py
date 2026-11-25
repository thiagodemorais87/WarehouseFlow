#!/usr/bin/env python3
"""Gera o PDF do modelo relacional (diagrama + relacionamentos + dicionário de dados)
e a versão em Mermaid, lendo os MODELOS do backend (nada é digitado à mão, então o
documento não diverge do código).

    python scripts/gerar_pdf_relacionamentos.py
    -> docs/Modelo_Relacional_WarehouseFlow.pdf
    -> docs/modelo-relacional.md

Requer: reportlab (pip install reportlab). Ele não faz parte do requirements.txt da API,
porque só é usado para gerar este documento.
"""

import math
import os
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "gerador-de-documentacao")

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER  # noqa: E402
from reportlab.lib.pagesizes import A4, landscape  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    Flowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from app.database import Base  # noqa: E402
import app.models  # noqa: E402,F401
import app.models.optimization_run  # noqa: E402,F401


SCHEMA_SQL = ROOT / "backend" / "database" / "schema.sql"
OUT_PDF = ROOT / "docs" / "Modelo_Relacional_WarehouseFlow.pdf"
OUT_MD = ROOT / "docs" / "modelo-relacional.md"

# fontes
_FONT, _BOLD = "Helvetica", "Helvetica-Bold"
for regular, bold in [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]:
    if Path(regular).exists() and Path(bold).exists():
        pdfmetrics.registerFont(TTFont("DejaVu", regular))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", bold))
        pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold",
                                      italic="DejaVu", boldItalic="DejaVu-Bold")
        _FONT, _BOLD = "DejaVu", "DejaVu-Bold"

AZUL = colors.HexColor("#1F3A5F")
AZUL_CLARO = colors.HexColor("#E8EEF6")
CINZA = colors.HexColor("#5F6B7A")
VERDE = colors.HexColor("#2E7D4F")
LARANJA = colors.HexColor("#B45F06")

# conhecimento de negócio
# Descrição curta de cada tabela e de cada relacionamento (FK).
TABELAS = {
    "roles": "Perfis de acesso (ADMIN, GESTOR, OPERADOR).",
    "users": "Usuários do sistema; cada um tem um perfil.",
    "warehouses": "Armazéns (depósitos).",
    "locations": "Posições físicas (corredor, estante, prateleira) de um armazém.",
    "products": "Catálogo de produtos (SKU único).",
    "stock": "Saldo de um produto em uma posição (um registro por produto + posição).",
    "orders": "Pedidos de entrada (INBOUND) ou saída (OUTBOUND).",
    "order_items": "Itens (produto + quantidade) de um pedido.",
    "tasks": "Tarefas operacionais (separação, armazenagem) ligadas a um pedido.",
    "optimization_results": "Sugestão de posição/rota gerada para uma tarefa.",
    "optimization_runs": "Histórico de execuções do motor de rota (NN + 2-opt): quem, quando e resultado.",
}
REGRAS_FK = {
    "users.role_id": "Cada usuário tem um perfil. Excluir o perfil não apaga o usuário (fica sem perfil).",
    "locations.warehouse_id": "Posição pertence a um armazém. A API bloqueia (409) excluir armazém com posições.",
    "stock.product_id": "Saldo pertence a um produto. A API bloqueia (409) excluir produto com unidades em estoque.",
    "stock.location_id": "Saldo fica em uma posição. A API bloqueia (409) excluir posição com unidades.",
    "orders": "",
    "order_items.order_id": "Item pertence a um pedido; excluir o pedido remove os itens.",
    "order_items.product_id": "Item referencia um produto. Produto em pedido NÃO pode ser excluído (RESTRICT).",
    "tasks.order_id": "Tarefa pertence a um pedido. A API bloqueia (409) excluir pedido com tarefa não concluída.",
    "tasks.assigned_user_id": "Responsável pela tarefa (opcional). Excluir o usuário deixa a tarefa sem responsável.",
    "optimization_results.task_id": "Resultado pertence a uma tarefa; excluir a tarefa remove o resultado.",
    "optimization_results.suggested_location_id": "Posição sugerida (opcional). Sem ação de exclusão: a API bloqueia excluir posição usada.",
}
# Referências lógicas: SEM chave estrangeira de propósito (histórico/auditoria).
REFS_LOGICAS = [
    ("optimization_runs", "user_id", "users", "id",
     "Quem executou. Sem FK: o histórico sobrevive à exclusão do usuário (por isso guarda também user_email)."),
    ("optimization_runs", "order_id", "orders", "id",
     "Pedido otimizado (opcional, só quando source = by-order). Sem FK: o histórico sobrevive à exclusão do pedido."),
]
DESCRICOES = {
    "roles.name": "ADMIN, GESTOR ou OPERADOR (único).",
    "users.email": "Login do usuário (único).",
    "users.password_hash": "Hash bcrypt; a senha nunca é guardada.",
    "users.is_active": "Usuário inativo não consegue entrar.",
    "locations.code": "Código único da posição (ex.: A1-01-A).",
    "locations.is_active": "Posição inativa não recebe estoque.",
    "products.sku": "Código único do produto.",
    "products.weight": "Peso em kg (>= 0).",
    "products.volume": "Volume em m3 (>= 0).",
    "stock.quantity": "Saldo atual (>= 0); a API limita a 1.000.000.",
    "orders.type": "INBOUND (entrada) ou OUTBOUND (saída).",
    "orders.status": "PENDING, PROCESSING, COMPLETED ou CANCELLED.",
    "order_items.quantity": "Quantidade pedida (> 0); a API limita a 1.000.000.",
    "tasks.type": "PICKING, PUTAWAY ou REPLENISHMENT.",
    "tasks.status": "PENDING, IN_PROGRESS ou COMPLETED.",
    "optimization_results.score": "Pontuação/custo calculado pelo algoritmo.",
    "optimization_runs.source": "route (localizações enviadas) ou by-order (pedido OUTBOUND).",
    "optimization_runs.original_route": "Rota na ordem original (JSONB, lista de códigos).",
    "optimization_runs.nearest_neighbor_route": "Rota após o vizinho mais próximo (JSONB).",
    "optimization_runs.two_opt_route": "Rota final após o 2-opt (JSONB).",
    "optimization_runs.distance_reduction": "distance_before - distance_after.",
    "optimization_runs.reduction_percent": "distance_reduction / distance_before * 100.",
    "optimization_runs.execution_time_ms": "Tempo de execução do motor, em milissegundos.",
}

# leitura do metadata
def tabelas():
    return sorted(Base.metadata.tables.values(), key=lambda t: ORDEM.index(t.name) if t.name in ORDEM else 99)

ORDEM = ["roles", "users", "warehouses", "locations", "products", "stock", "orders",
         "order_items", "tasks", "optimization_results", "optimization_runs"]


def ler_ddl() -> dict[str, dict[str, dict]]:
    """Lê o DDL OFICIAL (schema.sql): tipo, nulidade, default e comentário de cada coluna.

    Os tipos vêm do DDL (e não do ORM) porque é o DDL que o Compose executa: o ORM, por
    exemplo, calcula VARCHAR(13) para um Enum, enquanto o banco tem VARCHAR(30).
    """
    sql = SCHEMA_SQL.read_text(encoding="utf-8")
    tabelas_ddl: dict[str, dict[str, dict]] = {}
    for m in re.finditer(r"CREATE TABLE (?:IF NOT EXISTS )?(\w+) \((.*?)\n\);", sql, re.S):
        colunas: dict[str, dict] = {}
        for linha in m.group(2).splitlines():
            codigo, _, comentario = linha.partition("--")
            codigo = codigo.strip().rstrip(",").strip()
            if not codigo or re.match(r"(CONSTRAINT|UNIQUE|PRIMARY|CHECK|FOREIGN)\b", codigo, re.I):
                continue
            nome, _, resto = codigo.partition(" ")
            tipo = re.match(r"(DOUBLE PRECISION|[A-Za-z]+(?:\(\s*\d+\s*(?:,\s*\d+\s*)?\))?)", resto).group(1)
            padrao = re.search(r"DEFAULT\s+('[^']*'|[^\s,]+)", resto, re.I)
            colunas[nome] = {
                "tipo": tipo.upper().replace(" ", "") if "(" in tipo else tipo.upper(),
                "nulo": not re.search(r"NOT NULL|PRIMARY KEY", resto, re.I),
                "pk": bool(re.search(r"PRIMARY KEY", resto, re.I)),
                "unico": bool(re.search(r"\bUNIQUE\b", resto, re.I)),
                "padrao": padrao.group(1) if padrao else "",
                "comentario": comentario.strip(),
            }
        tabelas_ddl[m.group(1)] = colunas
    return tabelas_ddl


DDL = ler_ddl()


def fks():
    """(tabela_filha, coluna, tabela_pai, coluna_pai, on_delete, obrigatória)"""
    saida = []
    for t in tabelas():
        for fk in sorted(t.foreign_keys, key=lambda f: f.parent.name):
            saida.append((t.name, fk.parent.name, fk.column.table.name, fk.column.name,
                          (fk.ondelete or "NO ACTION").upper(), not fk.parent.nullable))
    return saida


#  diagrama
# Coordenadas RELATIVAS ao diagrama (origem no canto inferior esquerdo; largura útil ~798, altura 440).
LARG = 120
COLS_X = [0, 169.5, 339, 508.5, 678]
LINHAS_Y = {0: 436, 1: 300, 2: 170, 3: 52}
POSICOES = {
    "optimization_runs": (2, 0),
    "roles": (0, 1), "users": (1, 1), "tasks": (2, 1), "orders": (3, 1), "order_items": (4, 1),
    "optimization_results": (1, 2), "locations": (2, 2), "stock": (3, 2), "products": (4, 2),
    "warehouses": (2, 3),
}


def colunas_chave(t):
    """PK, FKs, únicas e type/status: o suficiente para o diagrama (o resto vai no dicionário)."""
    fk_cols = {fk.parent.name for fk in t.foreign_keys}
    mostrar = []
    for c in t.columns:
        marca = "PK" if c.primary_key else ("FK" if c.name in fk_cols else ("UK" if c.unique else ""))
        if marca or c.name in ("type", "status", "name", "code", "sku", "email", "source"):
            mostrar.append((marca, c.name))
    if t.name == "optimization_runs":
        mostrar = [("PK", "id"), ("REF", "user_id"), ("REF", "order_id"), ("", "source"), ("", "executed_at")]
    return mostrar, len(t.columns) - len(mostrar)


class Diagrama(Flowable):
    def __init__(self, largura, altura):
        super().__init__()
        self.width, self.height = largura, altura

    # geometria
    def _caixa(self, nome):
        t = Base.metadata.tables[nome]
        linhas, resto = colunas_chave(t)
        col, lin = POSICOES[nome]
        altura = 16 + 11 * len(linhas) + (10 if resto > 0 else 0) + 4
        x, topo = COLS_X[col], LINHAS_Y[lin]
        return {"x": x, "y": topo - altura, "w": LARG, "h": altura, "linhas": linhas, "resto": resto}

    @staticmethod
    def _borda(caixa, alvo_x, alvo_y):
        """Ponto onde a reta centro->alvo cruza a borda da caixa."""
        cx, cy = caixa["x"] + caixa["w"] / 2, caixa["y"] + caixa["h"] / 2
        dx, dy = alvo_x - cx, alvo_y - cy
        if dx == 0 and dy == 0:
            return cx, cy
        escala = min((caixa["w"] / 2) / abs(dx) if dx else math.inf, (caixa["h"] / 2) / abs(dy) if dy else math.inf)
        return cx + dx * escala, cy + dy * escala

    def _rotulo(self, c, x, y, texto, cor):
        c.setFont(_BOLD, 7.5)
        c.setFillColor(cor)
        c.drawCentredString(x, y, texto)

    def draw(self):
        c = self.canv
        caixas = {n: self._caixa(n) for n in POSICOES}

        def ligar(filha, pai, rotulo_pai, rotulo_filha, meio, tracejado=False, cor=AZUL):
            a, b = caixas[pai], caixas[filha]
            ax, ay = a["x"] + a["w"] / 2, a["y"] + a["h"] / 2
            bx, by = b["x"] + b["w"] / 2, b["y"] + b["h"] / 2
            p1 = self._borda(a, bx, by)
            p2 = self._borda(b, ax, ay)
            c.saveState()
            c.setStrokeColor(cor)
            c.setLineWidth(1.1)
            if tracejado:
                c.setDash(4, 3)
            c.line(*p1, *p2)
            c.restoreState()
            vx, vy = p2[0] - p1[0], p2[1] - p1[1]
            n = math.hypot(vx, vy) or 1
            ox, oy = -vy / n * 7, vx / n * 7  # deslocamento perpendicular
            self._rotulo(c, p1[0] + vx / n * 11 + ox, p1[1] + vy / n * 11 + oy - 2, rotulo_pai, cor)
            self._rotulo(c, p2[0] - vx / n * 11 + ox, p2[1] - vy / n * 11 + oy - 2, rotulo_filha, cor)
            if meio:
                mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
                c.setFont(_FONT, 5.8)
                c.setFillColor(CINZA)
                largura_txt = c.stringWidth(meio, _FONT, 5.8)
                c.setFillColor(colors.white)
                c.rect(mx - largura_txt / 2 - 1.5, my - 3.4, largura_txt + 3, 8, stroke=0, fill=1)
                c.setFillColor(CINZA)
                c.drawCentredString(mx, my - 1.2, meio)

        for filha, col, pai, _, ond, obrig in fks():
            ligar(filha, pai, "1" if obrig else "0..1", "N", ond)
        for filha, col, pai, _, _ in REFS_LOGICAS:
            ligar(filha, pai, "1", "N", "ref. lógica", tracejado=True, cor=LARANJA)

        for nome, cx in caixas.items():
            t = Base.metadata.tables[nome]
            tracejada = nome == "optimization_runs"
            c.saveState()
            c.setFillColor(colors.white)
            c.setStrokeColor(LARANJA if tracejada else AZUL)
            c.setLineWidth(1.2)
            c.roundRect(cx["x"], cx["y"], cx["w"], cx["h"], 4, stroke=1, fill=1)
            c.setFillColor(LARANJA if tracejada else AZUL)
            c.roundRect(cx["x"], cx["y"] + cx["h"] - 16, cx["w"], 16, 4, stroke=0, fill=1)
            c.rect(cx["x"], cx["y"] + cx["h"] - 16, cx["w"], 8, stroke=0, fill=1)
            c.setFillColor(colors.white)
            c.setFont(_BOLD, 8.5)
            c.drawCentredString(cx["x"] + cx["w"] / 2, cx["y"] + cx["h"] - 11.5, nome)
            y = cx["y"] + cx["h"] - 16 - 10
            for marca, col in cx["linhas"]:
                cor_marca = {"PK": colors.HexColor("#B8860B"), "FK": VERDE, "UK": CINZA, "REF": LARANJA}.get(marca, CINZA)
                c.setFillColor(cor_marca)
                c.setFont(_BOLD, 6.5)
                c.drawString(cx["x"] + 5, y, marca)
                c.setFillColor(colors.black)
                c.setFont(_FONT, 7.2)
                c.drawString(cx["x"] + 24, y, col)
                y -= 11
            if cx["resto"] > 0:
                c.setFillColor(CINZA)
                c.setFont(_FONT, 6.3)
                c.drawString(cx["x"] + 5, y, f"+ {cx['resto']} colunas (ver dicionário)")
            c.restoreState()


# estilos
ss = getSampleStyleSheet()
BASE = ParagraphStyle("base", parent=ss["Normal"], fontName=_FONT, fontSize=8.6, leading=11.5)
PEQ = ParagraphStyle("peq", parent=BASE, fontSize=7.4, leading=9.4)
PEQ_B = ParagraphStyle("peqb", parent=PEQ, fontName=_BOLD)
CAB = ParagraphStyle("cab", parent=PEQ_B, textColor=colors.white)
H1 = ParagraphStyle("h1", parent=BASE, fontName=_BOLD, fontSize=15, leading=19, textColor=AZUL, spaceAfter=6)
H2 = ParagraphStyle("h2", parent=BASE, fontName=_BOLD, fontSize=11, leading=14, textColor=AZUL, spaceBefore=8, spaceAfter=4)
TIT = ParagraphStyle("tit", parent=H1, fontSize=24, leading=30, alignment=TA_CENTER)
SUB = ParagraphStyle("sub", parent=BASE, fontSize=11, leading=15, alignment=TA_CENTER, textColor=CINZA)


def tabela(dados, larguras, zebra=True):
    t = Table(dados, colWidths=larguras, repeatRows=1)
    estilo = [("BACKGROUND", (0, 0), (-1, 0), AZUL), ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#B8C2D0")),
              ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
              ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    if zebra:
        for i in range(1, len(dados)):
            if i % 2 == 0:
                estilo.append(("BACKGROUND", (0, i), (-1, i), AZUL_CLARO))
    t.setStyle(TableStyle(estilo))
    return t


def p(txt, estilo=PEQ):
    return Paragraph(txt, estilo)


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont(_FONT, 7)
    canvas.setFillColor(CINZA)
    w, _ = landscape(A4)
    canvas.drawString(22, 14, "WarehouseFlow - Modelo relacional (gerado a partir dos modelos do backend)")
    canvas.drawRightString(w - 22, 14, f"Página {doc.page}")
    canvas.restoreState()


# conteúdo
def construir():
    largura, altura = landscape(A4)
    util = largura - 44
    historia = []

    n_fk = len(fks())
    historia += [
        Spacer(1, 60), Paragraph("WarehouseFlow", TIT),
        Paragraph("Modelo Relacional: tabelas, relacionamentos e regras de integridade", SUB),
        Spacer(1, 14),
        Paragraph(f"Banco de dados PostgreSQL · {len(Base.metadata.tables)} tabelas · {n_fk} chaves estrangeiras · "
                  f"{len(REFS_LOGICAS)} referências lógicas · gerado em {date.today():%d/%m/%Y}", SUB),
        Spacer(1, 26),
        Paragraph("Como ler este documento", H2),
        Paragraph("<b>1. Diagrama</b>: visão geral das tabelas e de como se ligam. "
                  "<b>2. Relacionamentos</b>: cada chave estrangeira, a cardinalidade, se é obrigatória e o que acontece "
                  "na exclusão (ON DELETE). <b>3. Dicionário de dados</b>: todas as colunas de cada tabela, com tipo, "
                  "obrigatoriedade e regra. <b>4. Regras de integridade</b>: UNIQUE e CHECK aplicados no banco.", BASE),
        Spacer(1, 8),
        Paragraph("O DDL oficial é <b>backend/database/schema.sql</b> (usado pelo Docker Compose) e os dados de demonstração "
                  "estão em <b>backend/database/seed.sql</b>. Este PDF é gerado por <b>scripts/gerar_pdf_relacionamentos.py</b> "
                  "a partir dos modelos SQLAlchemy, e o teste <b>tests/test_schema_coerente.py</b> garante que schema.sql, "
                  "modelos e este documento descrevem o mesmo banco.", BASE),
        PageBreak(),
    ]

    # 1. diagrama
    historia.append(Paragraph("1. Diagrama de relacionamentos", H1))
    historia.append(Diagrama(util, 440))
    historia.append(Spacer(1, 6))
    historia.append(Paragraph(
        "<b>Legenda:</b> PK = chave primária · FK = chave estrangeira · UK = valor único · "
        "<font color='#B45F06'>REF</font> = referência lógica (sem FK) · linha contínua = FK, com a regra ON DELETE no meio · "
        "<font color='#B45F06'>linha tracejada</font> = referência lógica · "
        "<b>1</b> / <b>N</b> = cardinalidade (um pai para vários filhos) · <b>0..1</b> = pai opcional.", PEQ))
    historia.append(PageBreak())

    # 2. relacionamentos
    historia.append(Paragraph("2. Relacionamentos (chaves estrangeiras)", H1))
    dados = [[p("Tabela filha (N)", CAB), p("Coluna", CAB), p("Tabela pai (1)", CAB), p("Obrigatória?", CAB),
              p("ON DELETE", CAB), p("Regra", CAB)]]
    for filha, col, pai, colpai, ond, obrig in fks():
        regra = REGRAS_FK.get(f"{filha}.{col}", "")
        dados.append([p(f"<b>{filha}</b>"), p(col), p(f"<b>{pai}</b>.{colpai}"), p("Sim" if obrig else "Não (opcional)"),
                      p(ond), p(regra)])
    historia.append(tabela(dados, [88, 100, 90, 62, 62, util - 402]))
    historia.append(Spacer(1, 10))
    historia.append(Paragraph("Referências lógicas (sem chave estrangeira, de propósito)", H2))
    dados = [[p("Tabela", CAB), p("Coluna", CAB), p("Referencia", CAB), p("Motivo", CAB)]]
    for filha, col, pai, colpai, motivo in REFS_LOGICAS:
        dados.append([p(f"<b>{filha}</b>"), p(col), p(f"{pai}.{colpai}"), p(motivo)])
    historia.append(tabela(dados, [100, 70, 80, util - 250]))
    historia.append(Spacer(1, 10))
    historia.append(Paragraph("O que significa cada regra ON DELETE", H2))
    historia.append(tabela([
        [p("Regra", CAB), p("Efeito ao excluir o registro pai", CAB)],
        [p("<b>CASCADE</b>"), p("Os registros filhos são excluídos junto (ex.: excluir um pedido remove seus itens).")],
        [p("<b>RESTRICT</b>"), p("O banco recusa a exclusão enquanto existirem filhos (ex.: produto que consta em pedido).")],
        [p("<b>SET NULL</b>"), p("A coluna do filho vira NULL e o filho continua existindo (ex.: tarefa sem responsável).")],
        [p("<b>NO ACTION</b>"), p("O banco recusa a exclusão se houver filhos (equivale a RESTRICT na prática).")],
    ], [90, util - 90]))
    historia.append(PageBreak())

    # 3. dicionário de dados
    historia.append(Paragraph("3. Dicionário de dados", H1))
    for t in tabelas():
        fk_alvo = {fk.parent.name: f"{fk.column.table.name}.{fk.column.name}" for fk in t.foreign_keys}
        cabeca = Paragraph(f"{t.name}", H2)
        desc = Paragraph(TABELAS.get(t.name, ""), PEQ)
        dados = [[p("Coluna", CAB), p("Tipo", CAB), p("Nulo?", CAB), p("Chave", CAB), p("Padrão", CAB), p("Descrição", CAB)]]
        for nome, info in DDL[t.name].items():
            chave = "PK" if info["pk"] else ("FK -> " + fk_alvo[nome] if nome in fk_alvo else ("UK" if info["unico"] else ""))
            pad = "automático" if info["tipo"] == "SERIAL" else info["padrao"]
            descricao = DESCRICOES.get(f"{t.name}.{nome}") or info["comentario"]
            dados.append([p(f"<b>{nome}</b>"), p(info["tipo"]), p("-" if info["pk"] else ("Sim" if info["nulo"] else "Não")),
                          p(chave), p(pad), p(descricao)])
        historia.append(KeepTogether([cabeca, desc, Spacer(1, 2), tabela(dados, [118, 92, 38, 112, 92, util - 452])]))
    historia.append(PageBreak())

    # 4. regras de integridade
    historia.append(Paragraph("4. Regras de integridade no banco", H1))
    dados = [[p("Tabela", CAB), p("Tipo", CAB), p("Nome", CAB), p("Regra", CAB)]]
    for t in tabelas():
        # UNIQUE: o SQLAlchemy registra `unique=True` de mais de uma forma; deduplica por colunas
        unicos = {tuple(c.name for c in cons.columns) for cons in t.constraints
                  if cons.__class__.__name__ == "UniqueConstraint"}
        unicos |= {(col.name,) for col in t.columns if col.unique}
        for colunas in sorted(unicos):
            regra = (f"{colunas[0]} sem repetição" if len(colunas) == 1
                     else "combinação (" + ", ".join(colunas) + ") sem repetição")
            # nome gerado pelo PostgreSQL para UNIQUE sem nome no DDL
            dados.append([p(f"<b>{t.name}</b>"), p("UNIQUE"), p(f"{t.name}_{'_'.join(colunas)}_key"), p(regra)])
        # t.constraints é um conjunto: ordena por nome para o PDF sair igual a cada geração
        checks = sorted((c for c in t.constraints if c.__class__.__name__ == "CheckConstraint"),
                        key=lambda c: c.name or "")
        for cons in checks:
            dados.append([p(f"<b>{t.name}</b>"), p("CHECK"), p(cons.name or ""), p(str(cons.sqltext))])
    historia.append(tabela(dados, [100, 56, 190, util - 346]))
    historia.append(Spacer(1, 10))
    historia.append(Paragraph(
        "Além destas constraints, a API valida antes de gravar e responde com códigos HTTP claros: "
        "<b>400</b> para dado inválido (quantidade <= 0 ou acima de 1.000.000, texto vazio, valor nulo em PUT), "
        "<b>404</b> para registro inexistente e <b>409</b> para conflito (SKU ou código duplicado, estoque insuficiente, "
        "exclusão de registro com dependência). As constraints acima são a última barreira, caso algo escape da validação.", BASE))
    return historia


def gerar_mermaid() -> str:
    linhas = ["# Modelo relacional (Mermaid)", "",
              "> Gerado por `scripts/gerar_pdf_relacionamentos.py` a partir dos modelos. Não edite à mão.",
              "> O GitHub renderiza o diagrama abaixo. A versão para o relatório é `Modelo_Relacional_WarehouseFlow.pdf`.",
              "", "```mermaid", "erDiagram"]
    for filha, col, pai, _, _, obrig in fks():
        origem = "||" if obrig else "|o"
        linhas.append(f'    {pai} {origem}--o{{ {filha} : "{col}"')
    for filha, col, pai, _, _ in REFS_LOGICAS:
        linhas.append(f'    {pai} ||..o{{ {filha} : "{col} (ref. logica)"')
    for t in tabelas():
        fk_cols = {fk.parent.name for fk in t.foreign_keys}
        linhas.append(f"    {t.name} {{")
        for col in t.columns:
            tipo = DDL[t.name][col.name]["tipo"].split("(")[0].lower()
            marca = " PK" if col.primary_key else (" FK" if col.name in fk_cols else (" UK" if col.unique else ""))
            linhas.append(f"        {tipo} {col.name}{marca}")
        linhas.append("    }")
    linhas += ["```", "", "Linha contínua = chave estrangeira; pontilhada = referência lógica (sem FK).", ""]
    return "\n".join(linhas)


def main():
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT_PDF), pagesize=landscape(A4), leftMargin=22, rightMargin=22, topMargin=24,
                            bottomMargin=28, title="WarehouseFlow - Modelo Relacional",
                            author="WarehouseFlow", subject="Tabelas, relacionamentos e regras de integridade")
    doc.build(construir(), onFirstPage=rodape, onLaterPages=rodape)
    OUT_MD.write_text(gerar_mermaid(), encoding="utf-8")
    print(f"PDF:     {OUT_PDF.relative_to(ROOT)}")
    print(f"Mermaid: {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()