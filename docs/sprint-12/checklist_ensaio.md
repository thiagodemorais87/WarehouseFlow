# Checklist de ensaio — trecho do motor (Sprint 12)

Usar antes do ensaio completo da apresentação / gravação do vídeo horizontal.

## Ambiente

- [ ] `docker compose up --build` sobe sem erro
- [ ] UI responde em http://127.0.0.1:8080
- [ ] API/Swagger em http://127.0.0.1:8000/docs
- [ ] Login seed funciona (`admin@warehouseflow.com` / `admin123`)

## Dados

- [ ] Existe pelo menos um pedido **OUTBOUND** com itens e stock em locations ativas
- [ ] Anotar o `order_id` que será usado na demo
- [ ] Plano B: coordenadas manuais da fixture (FAR/NEAR) memorizadas ou em post-it

## Fluxo na UI

- [ ] Menu → **Otimização**
- [ ] Modo por pedido → otimizar → HTTP 200 e rotas visíveis
- [ ] Métricas: before, after, %, tempo em ms
- [ ] Abrir relatório picking **ou** dashboard com redução média
- [ ] (Opcional) Baixar CSV do picking

## Fala técnica (ensaiar em voz alta)

- [ ] Problema do zig-zag na ordem do pedido
- [ ] NN + 2-opt + Manhattan (não é ChatGPT / não é OR-Tools)
- [ ] Métricas calculadas, não inventadas
- [ ] Frase de fechamento do diferencial

## Contingência

| Falha | Ação |
|-------|------|
| Pedido sem posições (404) | Trocar para modo manual + fixture |
| Compose fora | Rodar `evidence_flow` no terminal e narrar os números 38→11 |
| Tela lenta | Já ter print S10/S11 de `/otimizacao` como backup visual |

## Assinatura do ensaio (motor)

| Item | OK? |
|------|-----|
| Roteiro [`roteiro_demo_motor.md`](roteiro_demo_motor.md) lido | |
| Timing ≤ 5 min no trecho do motor | |
| Fallback testado uma vez | |
