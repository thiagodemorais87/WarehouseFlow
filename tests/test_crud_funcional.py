"""Testes funcionais de CRUD: produtos, estoque, locais, pedidos e tarefas.

Cada entidade percorre o ciclo completo: criar, listar, buscar, editar, excluir
e confirmar que o registro excluído some (404).
"""

from tests.crud_support import api 


#  produtos
def test_produtos_crud_completo(api):
    criado = api.post(
        "/products/",
        {"sku": "PROD-100", "name": "Monitor", "description": "24 pol", "weight": 3.5, "volume": 0.025},
    )
    assert criado.status_code == 201
    produto = criado.json()
    assert produto["sku"] == "PROD-100" and produto["id"] > 0

    api.product(sku="PROD-200", name="Teclado Mecânico")
    assert {p["sku"] for p in api.get("/products/").json()} == {"PROD-100", "PROD-200"}
    assert [p["sku"] for p in api.get("/products/", params={"search": "teclado"}).json()] == ["PROD-200"]
    assert [p["sku"] for p in api.get("/products/", params={"search": "prod-1"}).json()] == ["PROD-100"]

    assert api.get(f"/products/{produto['id']}").json()["name"] == "Monitor"

    editado = api.put(f"/products/{produto['id']}", {"name": "Monitor 27", "weight": 4})
    assert editado.status_code == 200
    assert editado.json()["name"] == "Monitor 27" and editado.json()["sku"] == "PROD-100"

    assert api.delete(f"/products/{produto['id']}").status_code == 204
    assert api.get(f"/products/{produto['id']}").status_code == 404
    assert api.delete(f"/products/{produto['id']}").status_code == 404


def test_produtos_listagem_respeita_paginacao_em_ordem_de_id(api):
    ids = [api.product(sku=f"P-{i}", name=f"Produto {i}")["id"] for i in range(5)]
    pagina = api.get("/products/", params={"skip": 2, "limit": 2}).json()
    assert [p["id"] for p in pagina] == ids[2:4]


#  locais
def test_armazens_crud_completo(api):
    armazem = api.warehouse("Central")
    assert api.get("/locations/warehouses").json()[0]["name"] == "Central"
    assert api.get(f"/locations/warehouses/{armazem['id']}").json()["name"] == "Central"

    editado = api.put(f"/locations/warehouses/{armazem['id']}", {"address": "Av. Cais, 100"})
    assert editado.status_code == 200 and editado.json()["address"] == "Av. Cais, 100"

    assert api.delete(f"/locations/warehouses/{armazem['id']}").status_code == 204
    assert api.get(f"/locations/warehouses/{armazem['id']}").status_code == 404


def test_posicoes_crud_completo(api):
    wh = api.warehouse()
    posicao = api.location(wh["id"], "A1-01-A", aisle="A1", rack="01", shelf="A")
    api.location(wh["id"], "B1-01-A", aisle="B1")

    assert len(api.get("/locations").json()) == 2
    assert [p["code"] for p in api.get("/locations", params={"aisle": "B1"}).json()] == ["B1-01-A"]
    assert api.get(f"/locations/{posicao['id']}").json()["code"] == "A1-01-A"

    editada = api.put(f"/locations/{posicao['id']}", {"code": "A1-01-Z", "is_active": False})
    assert editada.status_code == 200
    assert editada.json()["code"] == "A1-01-Z" and editada.json()["is_active"] is False
    assert [p["code"] for p in api.get("/locations", params={"is_active": False}).json()] == ["A1-01-Z"]

    assert api.delete(f"/locations/{posicao['id']}").status_code == 204
    assert api.get(f"/locations/{posicao['id']}").status_code == 404


#  estoque
def test_estoque_crud_e_movimentacoes(api):
    produto = api.product()
    posicao = api.location(api.warehouse()["id"])

    saldo = api.stock(produto["id"], posicao["id"], quantity=10)
    assert saldo["quantity"] == 10
    assert len(api.get("/stock").json()) == 1
    assert len(api.get("/stock", params={"product_id": produto["id"]}).json()) == 1
    assert api.get("/stock", params={"product_id": 9999}).json() == []
    assert api.get(f"/stock/{saldo['id']}").json()["quantity"] == 10

    assert api.put(f"/stock/{saldo['id']}", {"quantity": 25}).json()["quantity"] == 25
    assert api.post(f"/stock/{saldo['id']}/inbound", {"quantity": 5}).json()["quantity"] == 30
    assert api.post(f"/stock/{saldo['id']}/outbound", {"quantity": 12}).json()["quantity"] == 18

    assert api.delete(f"/stock/{saldo['id']}").status_code == 204
    assert api.get(f"/stock/{saldo['id']}").status_code == 404


#  pedidos
def test_pedidos_crud_completo_com_itens(api):
    p1 = api.product("P-1", "Produto 1")
    p2 = api.product("P-2", "Produto 2")

    pedido = api.order([{"product_id": p1["id"], "quantity": 2}])
    assert pedido["status"] == "PENDING" and pedido["type"] == "OUTBOUND"
    assert pedido["items"][0]["quantity"] == 2
    api.order([{"product_id": p2["id"], "quantity": 1}], type="INBOUND")

    assert len(api.get("/orders/").json()) == 2
    assert [o["id"] for o in api.get("/orders/", params={"type": "INBOUND"}).json()] != [pedido["id"]]
    assert [o["id"] for o in api.get("/orders/", params={"status": "PENDING", "type": "OUTBOUND"}).json()] == [pedido["id"]]
    assert api.get(f"/orders/{pedido['id']}").json()["id"] == pedido["id"]

    editado = api.put(f"/orders/{pedido['id']}", {"status": "PROCESSING"})
    assert editado.status_code == 200 and editado.json()["status"] == "PROCESSING"

    # itens: adicionar, somar quantidade do mesmo produto, editar e remover
    novo = api.post(f"/orders/{pedido['id']}/items", {"product_id": p2["id"], "quantity": 4})
    assert novo.status_code == 201 and novo.json()["quantity"] == 4
    somado = api.post(f"/orders/{pedido['id']}/items", {"product_id": p2["id"], "quantity": 1})
    assert somado.json()["id"] == novo.json()["id"] and somado.json()["quantity"] == 5
    atualizado = api.put(f"/orders/{pedido['id']}/items/{novo.json()['id']}", {"quantity": 7})
    assert atualizado.json()["quantity"] == 7
    assert api.delete(f"/orders/{pedido['id']}/items/{novo.json()['id']}").status_code == 204
    assert len(api.get(f"/orders/{pedido['id']}").json()["items"]) == 1

    assert api.delete(f"/orders/{pedido['id']}").status_code == 204
    assert api.get(f"/orders/{pedido['id']}").status_code == 404


#  tarefas
def test_tarefas_crud_completo(api):
    pedido = api.order([{"product_id": api.product()["id"], "quantity": 1}])
    operador = api.user_id("operador")

    tarefa = api.task(pedido["id"], assigned_user_id=operador)
    assert tarefa["status"] == "PENDING" and tarefa["assigned_user_id"] == operador
    api.task(pedido["id"], type="PUTAWAY")

    assert len(api.get("/tasks/").json()) == 2
    assert [t["id"] for t in api.get("/tasks/", params={"type": "PUTAWAY"}).json()] != [tarefa["id"]]
    assert [t["id"] for t in api.get("/tasks/", params={"assigned_user_id": operador}).json()] == [tarefa["id"]]
    assert len(api.get("/tasks/", params={"order_id": pedido["id"]}).json()) == 2
    assert api.get(f"/tasks/{tarefa['id']}").json()["id"] == tarefa["id"]

    editada = api.put(f"/tasks/{tarefa['id']}", {"status": "IN_PROGRESS"})
    assert editada.status_code == 200 and editada.json()["status"] == "IN_PROGRESS"

    # o operador só enxerga e altera as próprias tarefas
    minhas = api.get("/tasks/", who="operador").json()
    assert [t["id"] for t in minhas] == [tarefa["id"]]
    concluida = api.put(f"/tasks/{tarefa['id']}", {"status": "COMPLETED"}, who="operador")
    assert concluida.status_code == 200 and concluida.json()["status"] == "COMPLETED"

    assert api.delete(f"/tasks/{tarefa['id']}").status_code == 204
    assert api.get(f"/tasks/{tarefa['id']}").status_code == 404