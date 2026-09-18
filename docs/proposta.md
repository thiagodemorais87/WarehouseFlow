# WarehouseFlow — Proposta Oficial do Projeto

Documento de referência para atender ao feedback acadêmico: **diferencial computacional** (otimização própria + métricas) e coerência problema → solução.

> Documento complementar: [optimization.md](optimization.md) · [cronograma.md](cronograma.md) (prazos oficiais das 12 sprints + entrega final 05/12) · PDF Sprint 01: [Sprint01_WarehouseFlow_8MB.pdf](Sprint01_WarehouseFlow_8MB.pdf)

---

## 1. Problema

Em operações de armazém, a **ordem de visita às posições** durante o picking costuma seguir a ordem dos itens do pedido (ou uma ordem operacional ad hoc). Isso gera:

* deslocamentos longos e repetitivos entre corredores;
* tempo de separação maior do que o necessário;
* dificuldade de medir ganho real de eficiência;
* sistemas de gestão que apenas **cadastram e consultam** estoque (CRUD), sem calcular rotas melhores.

**Pergunta central:** como reduzir o deslocamento do operador na separação de pedidos, com um método computacional próprio, transparente e mensurável?

---

## 2. Por que não basta um WMS convencional?

Um sistema convencional de gestão de estoque resolve:

* cadastro de produtos, posições, pedidos e usuários;
* consulta e atualização de saldos.

Isso é necessário, mas **não é o diferencial**. Sem um motor que **reordene visitas** e **reporte métricas**, a proposta permanece apenas um CRUD de armazém — exatamente a crítica de coerência parcial recebida na avaliação inicial.

---

## 3. Solução — WarehouseFlow

O WarehouseFlow combina:

1. **Camada operacional (CRUD + PostgreSQL):** produtos, estoque, posições, pedidos, tarefas e usuários.
2. **Diferencial computacional — motor de otimização de picking** (implementação própria em Python):
   * heurística **Nearest Neighbor** (vizinho mais próximo);
   * melhoria local **2-opt**;
   * distância **Manhattan** (adequada a corredores em grade);
   * **sem** solvers externos (OR-Tools, NetworkX, etc.).

### Fluxo problema → solução

```text
Pedido / lista de posições (ordem original)
              ↓
     Distâncias Manhattan
              ↓
     Nearest Neighbor (rota gulosa)
              ↓
     2-opt (melhoria local)
              ↓
Rota sugerida + métricas de desempenho
```

Endpoint de demonstração: `POST /optimization/route`  
Código: `backend/optimization/` · API: `backend/app/routes/optimization.py`

---

## 4. Métricas de desempenho (obrigatórias)

O motor **calcula** (não inventa) e devolve:

| Métrica | Significado |
|---------|-------------|
| `distance_before` | Distância da rota original (ordem de entrada) |
| `nearest_neighbor_distance` | Distância após NN |
| `two_opt_distance` / `distance_after` | Distância após 2-opt |
| `distance_reduction` | `distance_before - distance_after` |
| `reduction_percent` | Redução percentual (0 se `distance_before == 0`) |
| `execution_time_ms` | Tempo de execução do algoritmo |
| `locations_count` | Quantidade de posições visitadas |

Também retorna as rotas (`original_route`, `nearest_neighbor_route`, `two_opt_route`) para auditoria e demonstração em aula.

Garantia local: `two_opt_distance ≤ nearest_neighbor_distance`. A comparação com a rota original é **honesta** (em casos patológicos a rota final pode não melhorar — e isso é reportado).

Detalhamento técnico: [optimization.md](optimization.md).

---

## 5. O que já está implementado vs. o que é CRUD de apoio

| Camada | Papel | Status |
|--------|-------|--------|
| Motor NN + 2-opt + métricas | Diferencial computacional | Implementado + testes |
| `POST /optimization/route` | Exposição do diferencial via API | Implementado |
| PostgreSQL + CRUD (produtos, estoque, pedidos, etc.) | Base operacional | Implementado |
| Integração `order_id` → posições → motor | Liga CRUD ao motor | Planejada (ver cronograma) |
| Login JWT + perfis | Controle de acesso | Sprint de auth (outro integrante) |
| Telas HTML completas | UX | Em evolução (shell de login existe) |

---

## 6. Coerência com o feedback da professora

| Exigência | Como o projeto responde |
|-----------|-------------------------|
| Incluir IA **ou** otimização própria | Otimização própria (NN + 2-opt), sem biblioteca de solver |
| Métricas de desempenho | Distâncias, redução %, tempo em ms |
| Não ser só gestão convencional | CRUD é apoio; o diferencial é o motor |
| Cronograma com sprints semanais e datas | [cronograma.md](cronograma.md) |

---

## 7. Equipe

| Integrante | Matrícula |
|------------|----------:|
| Gabriel George de Araújo Figueiredo | 01605236 |
| Guilherme Branco Ferrario | 01596391 |
| João Pedro Silva de Araujo | 01606470 |
| Sérgio José de Araújo Júnior | 01590694 |
| Thiago de Morais Gonçalves | 01609695 |

**Turma:** 8MA — Manhã · **Disciplina:** Fábrica de Software

---

## 8. Como demonstrar o diferencial

```bash
docker compose up --build
# Swagger: http://127.0.0.1:8000/docs  →  POST /optimization/route
pytest -q
```

Payload de exemplo e interpretação das métricas: [optimization.md](optimization.md).
