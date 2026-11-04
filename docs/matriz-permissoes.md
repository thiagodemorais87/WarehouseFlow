# Matriz de permissões (evidência 401/403)

Gerada automaticamente por `tests/test_matriz_permissoes.py`.

- 🔒 **401**: sem login ou token inválido/expirado.
- ⛔ **403**: logado, mas o perfil não tem permissão.
- 💥 **500**: passou pela autorização, mas o endpoint quebrou (bug a corrigir).
- ✅ **status**: passou pela autorização. O número é a resposta do endpoint (404 ou 422 porque o teste usa um id inexistente e corpo vazio).

| Método | Endpoint | sem token | token inválido | ADMIN | GESTOR | OPERADOR |
|---|---|---|---|---|---|---|
| GET | `/auth/me` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| GET | `/locations` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| POST | `/locations` | 🔒 401 | 🔒 401 | ✅ 400 | ✅ 400 | ⛔ 403 |
| GET | `/locations/warehouses` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| POST | `/locations/warehouses` | 🔒 401 | 🔒 401 | ✅ 400 | ✅ 400 | ⛔ 403 |
| DELETE | `/locations/warehouses/{warehouse_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ⛔ 403 |
| GET | `/locations/warehouses/{warehouse_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ✅ 404 |
| PUT | `/locations/warehouses/{warehouse_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ⛔ 403 |
| DELETE | `/locations/{location_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ⛔ 403 |
| GET | `/locations/{location_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ✅ 404 |
| PUT | `/locations/{location_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ⛔ 403 |
| GET | `/optimization-results/` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| POST | `/optimization-results/` | 🔒 401 | 🔒 401 | ✅ 400 | ✅ 400 | ✅ 400 |
| GET | `/optimization-results/task/{task_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ✅ 404 |
| DELETE | `/optimization-results/{result_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ⛔ 403 |
| GET | `/optimization-results/{result_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ✅ 404 |
| GET | `/optimization/orders/{order_id}/pick-locations` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ✅ 404 |
| GET | `/optimization/reports/picking` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| GET | `/optimization/reports/picking.csv` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| GET | `/optimization/reports/summary` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| POST | `/optimization/route` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| POST | `/optimization/route/by-order` | 🔒 401 | 🔒 401 | ✅ 400 | ✅ 400 | ✅ 400 |
| GET | `/orders/` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| POST | `/orders/` | 🔒 401 | 🔒 401 | ✅ 400 | ✅ 400 | ✅ 400 |
| DELETE | `/orders/{order_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ⛔ 403 |
| GET | `/orders/{order_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ✅ 404 |
| PUT | `/orders/{order_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ✅ 404 |
| POST | `/orders/{order_id}/items` | 🔒 401 | 🔒 401 | ✅ 400 | ✅ 400 | ✅ 400 |
| DELETE | `/orders/{order_id}/items/{item_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ✅ 404 |
| PUT | `/orders/{order_id}/items/{item_id}` | 🔒 401 | 🔒 401 | ✅ 400 | ✅ 400 | ✅ 400 |
| GET | `/products/` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| POST | `/products/` | 🔒 401 | 🔒 401 | ✅ 400 | ✅ 400 | ⛔ 403 |
| DELETE | `/products/{product_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ⛔ 403 |
| GET | `/products/{product_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ✅ 404 |
| PUT | `/products/{product_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ⛔ 403 |
| GET | `/reports/dashboard` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| GET | `/reports/orders` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ⛔ 403 |
| GET | `/reports/orders.csv` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ⛔ 403 |
| GET | `/reports/stock-movements` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ⛔ 403 |
| GET | `/reports/stock-movements.csv` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ⛔ 403 |
| GET | `/stock` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| POST | `/stock` | 🔒 401 | 🔒 401 | ✅ 400 | ✅ 400 | ✅ 400 |
| DELETE | `/stock/{stock_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ⛔ 403 |
| GET | `/stock/{stock_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ✅ 404 |
| PUT | `/stock/{stock_id}` | 🔒 401 | 🔒 401 | ✅ 400 | ✅ 400 | ✅ 400 |
| POST | `/stock/{stock_id}/inbound` | 🔒 401 | 🔒 401 | ✅ 400 | ✅ 400 | ✅ 400 |
| POST | `/stock/{stock_id}/outbound` | 🔒 401 | 🔒 401 | ✅ 400 | ✅ 400 | ✅ 400 |
| GET | `/tasks/` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| POST | `/tasks/` | 🔒 401 | 🔒 401 | ✅ 400 | ✅ 400 | ✅ 400 |
| DELETE | `/tasks/{task_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ⛔ 403 |
| GET | `/tasks/{task_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ✅ 404 |
| PUT | `/tasks/{task_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ✅ 404 |
| GET | `/users/` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| POST | `/users/` | 🔒 401 | 🔒 401 | ✅ 400 | ⛔ 403 | ⛔ 403 |
| GET | `/users/roles/` | 🔒 401 | 🔒 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| POST | `/users/roles/` | 🔒 401 | 🔒 401 | ✅ 400 | ⛔ 403 | ⛔ 403 |
| DELETE | `/users/{user_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ⛔ 403 | ⛔ 403 |
| GET | `/users/{user_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ✅ 404 | ✅ 404 |
| PUT | `/users/{user_id}` | 🔒 401 | 🔒 401 | ✅ 404 | ⛔ 403 | ⛔ 403 |
