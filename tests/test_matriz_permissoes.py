"""Matriz de permissões: evidências de 401 (sem login) e 403 (sem permissão).

Percorre TODAS as rotas privadas da API com cinco "identidades":
sem token, token inválido, ADMIN, GESTOR e OPERADOR.

- test_toda_rota_privada_exige_token: falha se alguém criar uma rota nova sem proteção.
- test_regras_principais_por_perfil: mesmo endpoint com ADMIN liberado e outros bloqueados.
- test_gerar_arquivo_da_matriz: gera docs/matriz-permissoes.md (só quando GERAR_MATRIZ=1).
"""

import os
import re
from pathlib import Path

import pytest

from app.main import app
from tests.test_auth import client, login  # noqa: F401  (client é uma fixture)

# Rotas públicas de propósito (todas as outras exigem login)
PUBLICAS = {("POST", "/auth/login"), ("GET", "/health"), ("GET", "/")}

PERFIS = ("admin", "gestor", "operador")
COLUNAS = ("sem token", "token inválido", "ADMIN", "GESTOR", "OPERADOR")


def rotas_da_api():
    """Lista (método, caminho) de cada rota privada documentada no /docs (páginas HTML ficam de fora)."""
    esquema = app.openapi()
    rotas = []
    for caminho, operacoes in esquema.get("paths", {}).items():
        for metodo, operacao in operacoes.items():
            metodo = metodo.upper()
            if metodo not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                continue
            if "Frontend" in operacao.get("tags", []):
                continue
            if (metodo, caminho) in PUBLICAS:
                continue
            rotas.append((metodo, caminho))
    return sorted(set(rotas), key=lambda r: (r[1], r[0]))


def montar_matriz(client):
    """Chama cada rota com cada identidade e devolve [(método, caminho, {coluna: status})]."""
    tokens = {who: login(client, who).json()["access_token"] for who in PERFIS}
    # O login grava um cookie; limpamos para o teste "sem token" valer de verdade
    client.cookies.clear()

    cabecalhos = {
        "sem token": {},
        "token inválido": {"Authorization": "Bearer token-falso"},
        "ADMIN": {"Authorization": f"Bearer {tokens['admin']}"},
        "GESTOR": {"Authorization": f"Bearer {tokens['gestor']}"},
        "OPERADOR": {"Authorization": f"Bearer {tokens['operador']}"},
    }

    rotas = rotas_da_api()
    assert len(rotas) >= 20, (
        f"A matriz achou só {len(rotas)} rotas privadas "
        f"({len(app.routes)} rotas registradas no app). Algo está errado na descoberta das rotas."
    )

    linhas = []
    for metodo, caminho in rotas:
        # Id inexistente: quem tem permissão recebe 404 e nada é apagado nem alterado
        url = re.sub(r"\{[^}]+\}", "999999", caminho)
        corpo = {} if metodo in ("POST", "PUT", "PATCH") else None
        resultado = {}
        for coluna in COLUNAS:
            try:
                resp = client.request(metodo, url, headers=cabecalhos[coluna], json=corpo)
                resultado[coluna] = resp.status_code
            except Exception:
                # O TestClient relança erros internos do servidor; registramos como 500
                resultado[coluna] = 500
        linhas.append((metodo, caminho, resultado))
    return linhas


def normalizar(caminho):
    """/users/ e /users são o mesmo recurso; /tasks/{task_id} e /tasks/{id} também."""
    return re.sub(r"\{[^}]*\}", "{}", caminho).rstrip("/")


def buscar(matriz, metodo, caminho):
    """Acha a linha da matriz ignorando a barra final e o nome dos parâmetros."""
    alvo = normalizar(caminho)
    for (m, c), resultado in matriz.items():
        if m == metodo and normalizar(c) == alvo:
            return resultado
    parecidas = sorted(c for (m, c) in matriz if m == metodo and alvo.split("/")[1] in c)
    raise AssertionError(
        f"Rota não encontrada na matriz: {metodo} {caminho}. "
        f"Rotas {metodo} parecidas: {parecidas}"
    )


def liberado(status):
    """Passou pela autorização (o status real pode ser 404/422 porque o teste usa id e corpo vazios)."""
    return status not in (401, 403)


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

def test_toda_rota_privada_exige_token(client):
    problemas = []
    for metodo, caminho, res in montar_matriz(client):
        for situacao in ("sem token", "token inválido"):
            if res[situacao] != 401:
                problemas.append(f"{metodo} {caminho} ({situacao}) respondeu {res[situacao]}")
    assert not problemas, "Rotas privadas sem proteção:\n" + "\n".join(problemas)


def test_nenhuma_rota_responde_500(client):
    quebradas = [
        f"{metodo} {caminho} ({coluna})"
        for metodo, caminho, res in montar_matriz(client)
        for coluna in COLUNAS
        if res[coluna] >= 500
    ]
    assert not quebradas, "Rotas com erro interno (500):\n" + "\n".join(quebradas)


def test_regras_principais_por_perfil(client):
    matriz = {(m, c): r for m, c, r in montar_matriz(client)}

    # Usuários: qualquer logado consulta (a tela de tarefas lista os responsáveis),
    # mas só ADMIN cria, edita e apaga
    r = buscar(matriz, "GET", "/users/")
    assert liberado(r["ADMIN"])
    assert liberado(r["GESTOR"])
    assert liberado(r["OPERADOR"])

    for metodo, caminho in (("POST", "/users/"), ("PUT", "/users/{id}"), ("DELETE", "/users/{id}")):
        r = buscar(matriz, metodo, caminho)
        assert liberado(r["ADMIN"]), f"{metodo} {caminho}: ADMIN deveria passar"
        assert r["GESTOR"] == 403, f"{metodo} {caminho}: GESTOR deveria levar 403"
        assert r["OPERADOR"] == 403, f"{metodo} {caminho}: OPERADOR deveria levar 403"

    # Produtos: ADMIN e GESTOR criam, OPERADOR não
    r = buscar(matriz, "POST", "/products/")
    assert liberado(r["ADMIN"])
    assert liberado(r["GESTOR"])
    assert r["OPERADOR"] == 403

    # Relatório de pedidos: ADMIN e GESTOR, não o OPERADOR
    r = buscar(matriz, "GET", "/reports/orders")
    assert liberado(r["ADMIN"])
    assert liberado(r["GESTOR"])
    assert r["OPERADOR"] == 403

    # Apagar tarefa: ADMIN e GESTOR, não o OPERADOR
    r = buscar(matriz, "DELETE", "/tasks/{id}")
    assert liberado(r["ADMIN"])
    assert liberado(r["GESTOR"])
    assert r["OPERADOR"] == 403

    # Estoque: o OPERADOR movimenta (entrada), mas não apaga registro
    assert liberado(buscar(matriz, "POST", "/stock/{id}/inbound")["OPERADOR"])
    assert buscar(matriz, "DELETE", "/stock/{id}")["OPERADOR"] == 403


@pytest.mark.skipif(not os.getenv("GERAR_MATRIZ"), reason="defina GERAR_MATRIZ=1 para gerar o arquivo")
def test_gerar_arquivo_da_matriz(client):
    linhas = montar_matriz(client)

    def celula(status):
        if status == 401:
            return "🔒 401"
        if status == 403:
            return "⛔ 403"
        if status >= 500:
            return f"💥 {status}"
        return f"✅ {status}"

    texto = [
        "# Matriz de permissões (evidência 401/403)",
        "",
        "Gerada automaticamente por `tests/test_matriz_permissoes.py`.",
        "",
        "- 🔒 **401**: sem login ou token inválido/expirado.",
        "- ⛔ **403**: logado, mas o perfil não tem permissão.",
        "- 💥 **500**: passou pela autorização, mas o endpoint quebrou (bug a corrigir).",
        "- ✅ **status**: passou pela autorização. O número é a resposta do endpoint "
        "(404 ou 422 porque o teste usa um id inexistente e corpo vazio).",
        "",
        "| Método | Endpoint | " + " | ".join(COLUNAS) + " |",
        "|---|---|" + "---|" * len(COLUNAS),
    ]
    for metodo, caminho, res in linhas:
        texto.append(f"| {metodo} | `{caminho}` | " + " | ".join(celula(res[c]) for c in COLUNAS) + " |")

    destino = Path(__file__).resolve().parents[1] / "docs" / "matriz-permissoes.md"
    destino.write_text("\n".join(texto) + "\n", encoding="utf-8")
    assert destino.exists()