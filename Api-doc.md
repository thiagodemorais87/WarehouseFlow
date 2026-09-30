# WarehouseFlow --- Documentação da API e Casos de Teste

## Visão geral

Este documento apresenta as rotas da API do **WarehouseFlow** e os respetivos casos de teste evidenciados durante a Sprint 04[cite: 1].

A API foi executada localmente e testada utilizando o Postman[cite: 1].

**URL base utilizada nos testes:**

``` text
http://localhost:8000
```[cite: 1]

> **Observação:** as rotas abaixo correspondem às rotas identificadas nas requisições e evidências apresentadas durante os testes da Sprint 04[cite: 1].

---

## 1. Produtos

### POST `/products/`

Cria um novo produto[cite: 1].

**Exemplo de requisição:**

``` json
{
  "sku": "PROD-SPRINT4-001",
  "name": "Produto Teste Sprint 4",
  "description": "Produto criado para testes automatizados",
  "weight": 1.5,
  "volume": 0.02
}
```[cite: 1]

**Resposta observada:**

``` text
201 Created
```[cite: 1]

A resposta retornou os dados do produto criado, incluindo seu `id`[cite: 1].

---

### GET `/products/`

Lista os produtos cadastrados[cite: 1].

**Método:** `GET`[cite: 1]

**Resposta esperada:**

``` text
200 OK
```[cite: 1]

---

### GET `/products/{product_id}`

Consulta um produto específico pelo seu ID[cite: 1].

**Exemplo:**

``` text
GET /products/4
```[cite: 1]

---

### PUT `/products/{product_id}`

Edita um produto existente[cite: 1].

**Exemplo:**

``` text
PUT /products/4
```[cite: 1]

**Corpo:**

``` json
{
  "name": "Produto Teste Sprint 4 - Editado",
  "description": "Descrição atualizada",
  "weight": 2.0
}
```[cite: 1]

**Resposta observada:**

``` text
200 OK
```[cite: 1]

---

### DELETE `/products/{product_id}`

Exclui um produto existente[cite: 1].

**Exemplo:**

``` text
DELETE /products/4
```[cite: 1]

**Resposta observada:**

``` text
204 No Content
```[cite: 1]

---

## 2. Estoque

### POST `/stock/`

Cria ou ajusta um registro de estoque relacionando produto, localização e quantidade[cite: 1].

**Exemplo:**

``` json
{
  "product_id": 3,
  "location_id": 1,
  "quantity": 50
}
```[cite: 1]

**Resposta observada:**

``` text
201 Created
```[cite: 1]

**Exemplo de resposta:**

``` json
{
  "product_id": 3,
  "location_id": 1,
  "quantity": 50,
  "id": 4,
  "last_updated": "2026-09-24T20:35:05.377657"
}
```[cite: 1]

---

### GET `/stock/{product_id}`

Consulta o estoque associado a um produto pelo ID[cite: 1].

**Exemplo:**

``` text
GET /stock/3
```[cite: 1]

---

### GET `/stock/`

Lista os registros de estoque[cite: 1].

**Método:** `GET`[cite: 1]

---

### PUT `/stock/{stock_id}`

Atualiza a quantidade de um registro de estoque[cite: 1].

**Método:** `PUT`[cite: 1]

---

## 3. Localizações

As localizações representam posições dentro de um armazém[cite: 1].

### POST `/locations/`

Cria uma nova localização[cite: 1].

**Exemplo:**

``` json
{
  "warehouse_id": 2,
  "code": "A1-01-AB",
  "aisle": "A1",
  "rack": "01",
  "shelf": "A",
  "is_active": true
}
```[cite: 1]

**Resposta observada:**

``` text
201 Created
```[cite: 1]

**Exemplo de resposta:**

``` json
{
  "warehouse_id": 2,
  "code": "A1-01-AB",
  "aisle": "A1",
  "rack": "01",
  "shelf": "A",
  "is_active": true,
  "id": 6
}
```[cite: 1]

---

### GET `/locations/`

Lista as localizações cadastradas[cite: 1].

**Resposta observada:**

``` text
200 OK
```[cite: 1]

---

### GET `/locations/{location_id}`

Consulta uma localização específica pelo ID[cite: 1].

**Exemplo:**

``` text
GET /locations/1
```[cite: 1]

---

## 4. Validações

### Quantidade negativa no estoque

A API valida o campo `quantity` no cadastro/ajuste de estoque[cite: 1].

**Exemplo inválido:**

``` json
{
  "product_id": 3,
  "location_id": 1,
  "quantity": -10
}
```[cite: 1]

**Resposta observada:**

``` text
422 Unprocessable Entity
```[cite: 1]

A API informou que o valor deve ser:

``` text
greater than or equal to 0
```[cite: 1]

Ou seja, a quantidade de estoque não pode ser negativa[cite: 1].

---

## 5. Resumo das rotas

| Método | Rota | Função |
| :--- | :--- | :--- |
| POST | `/products/` | Criar produto[cite: 1] |
| GET | `/products/` | Listar produtos[cite: 1] |
| GET | `/products/{product_id}` | Consultar produto[cite: 1] |
| PUT | `/products/{product_id}` | Editar produto[cite: 1] |
| DELETE | `/products/{product_id}` | Excluir produto[cite: 1] |
| POST | `/stock/` | Criar/ajustar estoque[cite: 1] |
| GET | `/stock/{product_id}` | Consultar estoque por produto[cite: 1] |
| GET | `/stock/` | Listar estoque[cite: 1] |
| PUT | `/stock/{stock_id}` | Atualizar quantidade do estoque[cite: 1] |
| POST | `/locations/` | Criar localização[cite: 1] |
| GET | `/locations/` | Listar localizações[cite: 1] |
| GET | `/locations/{location_id}` | Consultar localização[cite: 1] |

---

## 6. Casos de Testes

### CT01 - Cadastrar Produto com Sucesso
* **Método:** `POST`[cite: 1]
* **Rota:** `/products/`[cite: 1]
* **Entrada:**
  ```json
  {
    "sku": "PROD-SPRINT4-001",
    "name": "Produto Teste Sprint 4",
    "description": "Produto criado para testes automatizados",
    "weight": 1.5,
    "volume": 0.02
  }
  ```[cite: 1]
* **Resultado Esperado:** Código `201 Created` e retorno dos dados do produto contendo o `id` gerado[cite: 1].

### CT02 - Consultar Lista de Produtos
* **Método:** `GET`[cite: 1]
* **Rota:** `/products/`[cite: 1]
* **Resultado Esperado:** Código `200 OK` e lista dos produtos cadastrados[cite: 1].

### CT03 - Consultar Produto por ID
* **Método:** `GET`[cite: 1]
* **Rota:** `/products/4`[cite: 1]
* **Resultado Esperado:** Código `200 OK` trazendo os dados do produto correspondente ao ID informado[cite: 1].

### CT04 - Editar Produto Existente
* **Método:** `PUT`[cite: 1]
* **Rota:** `/products/4`[cite: 1]
* **Entrada:**
  ```json
  {
    "name": "Produto Teste Sprint 4 - Editado",
    "description": "Descrição atualizada",
    "weight": 2.0
  }
  ```[cite: 1]
* **Resultado Esperado:** Código `200 OK` e dados do produto atualizados[cite: 1].

### CT05 - Excluir Produto Existente
* **Método:** `DELETE`[cite: 1]
* **Rota:** `/products/4`[cite: 1]
* **Resultado Esperado:** Código `204 No Content` confirmando a remoção do produto[cite: 1].

### CT06 - Criar/Ajustar Registro de Estoque Válido
* **Método:** `POST`[cite: 1]
* **Rota:** `/stock/`[cite: 1]
* **Entrada:**
  ```json
  {
    "product_id": 3,
    "location_id": 1,
    "quantity": 50
  }
  ```[cite: 1]
* **Resultado Esperado:** Código `201 Created` contendo o ID do registo de estoque e o carimbo de data/hora (`last_updated`)[cite: 1].

### CT07 - Tentar Cadastrar Estoque com Quantidade Negativa (Validação)
* **Método:** `POST`[cite: 1]
* **Rota:** `/stock/`[cite: 1]
* **Entrada:**
  ```json
  {
    "product_id": 3,
    "location_id": 1,
    "quantity": -10
  }
  ```[cite: 1]
* **Resultado Esperado:** Código `422 Unprocessable Entity` com mensagem informando que a quantidade deve ser `greater than or equal to 0`[cite: 1].

### CT08 - Consultar Estoque por Produto
* **Método:** `GET`[cite: 1]
* **Rota:** `/stock/3`[cite: 1]
* **Resultado Esperado:** Código `200 OK` e listagem das quantidades em estoque associadas ao produto informado[cite: 1].

### CT09 - Listar Todos os Registos de Estoque
* **Método:** `GET`[cite: 1]
* **Rota:** `/stock/`[cite: 1]
* **Resultado Esperado:** Código `200 OK` retornando a lista de todos os registos em estoque[cite: 1].

### CT10 - Atualizar Quantidade do Estoque
* **Método:** `PUT`[cite: 1]
* **Rota:** `/stock/{stock_id}`[cite: 1]
* **Resultado Esperado:** Código `200 OK` com os valores atualizados do registo de estoque[cite: 1].

### CT11 - Criar Localização com Sucesso
* **Método:** `POST`[cite: 1]
* **Rota:** `/locations/`[cite: 1]
* **Entrada:**
  ```json
  {
    "warehouse_id": 2,
    "code": "A1-01-AB",
    "aisle": "A1",
    "rack": "01",
    "shelf": "A",
    "is_active": true
  }
  ```[cite: 1]
* **Resultado Esperado:** Código `201 Created` retornando a localização cadastrada com o respetivo `id`[cite: 1].

### CT12 - Listar Localizações
* **Método:** `GET`[cite: 1]
* **Rota:** `/locations/`[cite: 1]
* **Resultado Esperado:** Código `200 OK` com a lista de localizações/posições de armazém cadastradas[cite: 1].

### CT13 - Consultar Localização por ID
* **Método:** `GET`[cite: 1]
* **Rota:** `/locations/1`[cite: 1]
* **Resultado Esperado:** Código `200 OK` exibindo os detalhes da localização solicitada[cite: 1].

---

## 7. Documentação interativa

Com a aplicação executando localmente, a documentação interativa da API pode ser acessada em:

``` text
http://localhost:8000/docs
```[cite: 1]

O Swagger permite visualizar as rotas disponíveis e realizar requisições diretamente contra a API[cite: 1].

---

**Projeto:** WarehouseFlow  
**Grupo:** 26  
**Turma:** 8MB  
**Sprint:** 04 --- Produtos e Estoque (com posições)[cite: 1]