# Roteiro de demonstração — Motor de otimização (diferencial)

**Duração sugerida no vídeo horizontal:** 3–5 minutos  
**Responsável pelo conteúdo técnico:** Thiago (motor)  
**Ambiente:** `docker compose up --build` · UI http://127.0.0.1:8080 · login `admin@warehouseflow.com` / `admin123`

---

## Objetivo da fala

Mostrar que o WarehouseFlow tem um **diferencial computacional próprio** (Nearest Neighbor + 2-opt, distância Manhattan), com **métricas calculadas**, integrado a pedido real — **sem OR-Tools / sem IA generativa**.

---

## Sequência (o que falar / o que clicar)

### 1. Problema (~30–45 s)

- **Falar:** “No picking, seguir a ordem do pedido pode fazer o operador zig-zag no armazém.”
- **Mostrar (opcional):** pedido OUTBOUND com vários itens / tela de pedidos.
- **Transição:** “O motor calcula uma sequência de visita que reduz o deslocamento.”

### 2. Otimizar por pedido (~60–90 s)

- Abrir **Otimização** (`/otimizacao`).
- Escolher modo **por pedido** (`order_id` de um OUTBOUND com stock).
- Clicar em otimizar.
- **Fallback se 404 / sem posições:** usar modo **manual** com a fixture acadêmica (FAR1, NEAR1, FAR2, NEAR2) — mesma narrativa de redução ~71%.

### 3. Métricas e rotas (~60–90 s)

Destacar na tela:

| Elemento | Frase sugerida |
|----------|----------------|
| Rota original | “Ordem do pedido — distância maior.” |
| Rota NN / 2-opt | “Heurística gulosa + melhoria local.” |
| `distance_before` → `distance_after` | “De X para Y unidades Manhattan.” |
| `reduction_percent` | “Redução de cerca de Z%.” |
| `execution_time_ms` | “Cálculo rápido, transparente.” |

### 4. Histórico / relatório (~30–45 s)

- Dashboard (KPI de redução média) **ou** relatório de picking / CSV.
- **Falar:** “Cada execução fica no histórico oficial (`optimization_runs`) para auditoria e indicadores.”

### 5. Fechamento (~15–20 s)

> “Diferencial do projeto: motor próprio de sequenciamento de picking, com métricas reais — não é só CRUD.”

---

## Números de referência (evidence_flow)

Úteis se a demo ao vivo falhar e precisar citar resultado reproduzível:

- `distance_before = 38` → `distance_after = 11` (~**71%**)
- Rota 2-opt: `START > NEAR1 > NEAR2 > FAR1 > FAR2`
- Comando: `$env:PYTHONPATH="backend"; python -m optimization.evidence_flow`

---

## Fora deste roteiro

Gravação YouTube/Instagram, edição e ensaio completo do time — material de apoio entregue; execução coletiva.
