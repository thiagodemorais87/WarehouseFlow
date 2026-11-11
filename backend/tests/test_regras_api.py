"""Validação da API e regras de negócio.

Cobre: quantidade <= 0, quantidade acima do limite, estoque insuficiente,
SKU duplicado, exclusão com dependência (409), `null` explícito em PUT e
referências inexistentes (404). Nenhum caso pode terminar em 500.
"""

import pytest

from tests.crud_support import Session, api 
from app import models

MAX = 1_000_000


# quantidade <= 0
@pytest.mark.parametrize("quantidade", [0, -1, -100])
def test_movimentacao_com_quantidade_invalida_retorna_400(api, quantidade):
    saldo = api.stock(api.product()["id"], api.location(api.warehouse()["id"])["id"], 10)
    for acao in ("inbound", "outbound"):
        resp = api.post(f"/stock/{saldo['id']}/{acao}", {"quantity": quantidade})
        assert resp.status_code == 400, (acao, resp.text)
    assert api.get(f"/stock/{saldo['id']}").json()["quantity"] == 10


@pytest.mark.parametrize("quantidade", [-1, -50])
def test_estoque_nao_aceita_quantidade_negativa(api, quantidade):
    produto = api.product()
    posicao = api.location(api.warehouse()["id"])
    resp = api.post("/stock", {"product_id": produto["id"], "location_id": posicao["id"], "quantity": quantidade})
    assert resp.status_code == 400
    saldo = api.stock(produto["id"], posicao["id"], 5)
    assert api.put(f"/stock/{saldo['id']}", {"quantity": quantidade}).status_code == 400
    assert api.get(f"/stock/{saldo['id']}").json()["quantity"] == 5


def test_estoque_aceita_quantidade_zero(api):
    saldo = api.stock(api.product()["id"], api.location(api.warehouse()["id"])["id"], 0)
    assert saldo["quantity"] == 0


@pytest.mark.parametrize("quantidade", [0, -3])
def test_itens_de_pedido_exigem_quantidade_positiva(api, quantidade):
    produto = api.product()
    resp = api.post("/orders/", {"type": "OUTBOUND", "items": [{"product_id": produto["id"], "quantity": quantidade}]})
    assert resp.status_code == 400
    assert api.get("/orders/").json() == []

    pedido = api.order([{"product_id": produto["id"], "quantity": 2}])
    assert api.post(f"/orders/{pedido['id']}/items", {"product_id": produto["id"], "quantity": quantidade}).status_code == 400
    item_id = pedido["items"][0]["id"]
    assert api.put(f"/orders/{pedido['id']}/items/{item_id}", {"quantity": quantidade}).status_code == 400
    assert api.get(f"/orders/{pedido['id']}").json()["items"][0]["quantity"] == 2


def test_pedido_sem_itens_retorna_400(api):
    assert api.post("/orders/", {"type": "INBOUND", "items": []}).status_code == 400


#  quantidade acima do limite
def test_quantidade_acima_do_limite_retorna_400_e_nao_500(api):
    """Postgres INTEGER estoura em 2.147.483.647: a API precisa barrar antes."""
    produto = api.product()
    posicao = api.location(api.warehouse()["id"])
    absurdo = 3_000_000_000

    assert api.post("/stock", {"product_id": produto["id"], "location_id": posicao["id"], "quantity": absurdo}).status_code == 400
    saldo = api.stock(produto["id"], posicao["id"], 10)
    assert api.put(f"/stock/{saldo['id']}", {"quantity": absurdo}).status_code == 400
    assert api.post(f"/stock/{saldo['id']}/inbound", {"quantity": absurdo}).status_code == 400
    assert api.post(f"/stock/{saldo['id']}/inbound", {"quantity": MAX}).status_code == 400  # 10 + MAX > MAX
    assert api.post(f"/stock/{saldo['id']}/outbound", {"quantity": absurdo}).status_code in (400, 409)

    assert api.post("/orders/", {"type": "INBOUND", "items": [{"product_id": produto["id"], "quantity": absurdo}]}).status_code == 400
    pedido = api.order([{"product_id": produto["id"], "quantity": MAX}])
    assert api.post(f"/orders/{pedido['id']}/items", {"product_id": produto["id"], "quantity": 1}).status_code == 400
    assert api.get(f"/orders/{pedido['id']}").json()["items"][0]["quantity"] == MAX


#  estoque insuficiente
def test_saida_maior_que_o_saldo_retorna_409_sem_alterar_o_estoque(api):
    saldo = api.stock(api.product()["id"], api.location(api.warehouse()["id"])["id"], 10)
    resp = api.post(f"/stock/{saldo['id']}/outbound", {"quantity": 11})
    assert resp.status_code == 409
    assert "insuficiente" in resp.json()["detail"].lower()
    assert api.get(f"/stock/{saldo['id']}").json()["quantity"] == 10


def test_saida_exata_zera_o_saldo_e_a_seguinte_e_barrada(api):
    saldo = api.stock(api.product()["id"], api.location(api.warehouse()["id"])["id"], 10)
    assert api.post(f"/stock/{saldo['id']}/outbound", {"quantity": 10}).json()["quantity"] == 0
    assert api.post(f"/stock/{saldo['id']}/outbound", {"quantity": 1}).status_code == 409


def test_estoque_duplicado_na_mesma_posicao_retorna_409(api):
    produto = api.product()
    posicao = api.location(api.warehouse()["id"])
    api.stock(produto["id"], posicao["id"], 1)
    resp = api.post("/stock", {"product_id": produto["id"], "location_id": posicao["id"], "quantity": 1})
    assert resp.status_code == 409


def test_posicao_inativa_nao_recebe_estoque(api):
    produto = api.product()
    posicao = api.location(api.warehouse()["id"], is_active=False)
    assert api.post("/stock", {"product_id": produto["id"], "location_id": posicao["id"], "quantity": 1}).status_code == 409


#  SKU duplicado
def test_sku_duplicado_retorna_409_na_criacao(api):
    api.product("DUP-1", "Primeiro")
    resp = api.post("/products/", {"sku": "DUP-1", "name": "Segundo"})
    assert resp.status_code == 409
    assert len(api.get("/products/").json()) == 1


def test_sku_duplicado_retorna_409_na_edicao(api):
    api.product("A-1", "A")
    outro = api.product("B-1", "B")
    assert api.put(f"/products/{outro['id']}", {"sku": "A-1"}).status_code == 409
    assert api.put(f"/products/{outro['id']}", {"sku": "B-1", "name": "B2"}).status_code == 200  # mesmo SKU: ok
    assert api.get(f"/products/{outro['id']}").json()["sku"] == "B-1"


def test_codigo_de_posicao_duplicado_retorna_409(api):
    wh = api.warehouse()
    api.location(wh["id"], "A1-01-A")
    assert api.post("/locations", {"warehouse_id": wh["id"], "code": "A1-01-A"}).status_code == 409
    outra = api.location(wh["id"], "A1-01-B")
    assert api.put(f"/locations/{outra['id']}", {"code": "A1-01-A"}).status_code == 409


#  exclusão com dependência 409
def test_excluir_produto_com_estoque_retorna_409(api):
    produto = api.product()
    api.stock(produto["id"], api.location(api.warehouse()["id"])["id"], 5)
    resp = api.delete(f"/products/{produto['id']}")
    assert resp.status_code == 409
    assert api.get(f"/products/{produto['id']}").status_code == 200
    assert len(api.get("/stock").json()) == 1


def test_excluir_produto_em_pedido_retorna_409(api):
    produto = api.product()
    api.order([{"product_id": produto["id"], "quantity": 1}])
    assert api.delete(f"/products/{produto['id']}").status_code == 409
    assert api.get(f"/products/{produto['id']}").status_code == 200


def test_excluir_produto_so_com_saldo_zerado_remove_o_produto_e_o_saldo(api):
    produto = api.product()
    saldo = api.stock(produto["id"], api.location(api.warehouse()["id"])["id"], 0)
    assert api.delete(f"/products/{produto['id']}").status_code == 204
    assert api.get(f"/stock/{saldo['id']}").status_code == 404


def test_excluir_posicao_com_unidades_retorna_409(api):
    posicao = api.location(api.warehouse()["id"])
    api.stock(api.product()["id"], posicao["id"], 3)
    assert api.delete(f"/locations/{posicao['id']}").status_code == 409
    assert api.get(f"/locations/{posicao['id']}").status_code == 200


def test_excluir_posicao_com_saldo_zerado_remove_posicao_e_saldo(api):
    posicao = api.location(api.warehouse()["id"])
    saldo = api.stock(api.product()["id"], posicao["id"], 0)
    assert api.delete(f"/locations/{posicao['id']}").status_code == 204
    assert api.get(f"/stock/{saldo['id']}").status_code == 404


def test_excluir_armazem_com_posicoes_retorna_409(api):
    wh = api.warehouse()
    api.location(wh["id"])
    assert api.delete(f"/locations/warehouses/{wh['id']}").status_code == 409
    assert api.get(f"/locations/warehouses/{wh['id']}").status_code == 200


def test_excluir_pedido_com_tarefa_aberta_retorna_409(api):
    pedido = api.order([{"product_id": api.product()["id"], "quantity": 1}])
    tarefa = api.task(pedido["id"])
    assert api.delete(f"/orders/{pedido['id']}").status_code == 409
    assert api.get(f"/orders/{pedido['id']}").status_code == 200
    assert api.get(f"/tasks/{tarefa['id']}").status_code == 200


def test_excluir_pedido_com_tarefas_concluidas_remove_pedido_e_tarefas(api):
    pedido = api.order([{"product_id": api.product()["id"], "quantity": 1}])
    tarefa = api.task(pedido["id"], status="COMPLETED")
    assert api.delete(f"/orders/{pedido['id']}").status_code == 204
    assert api.get(f"/tasks/{tarefa['id']}").status_code == 404


#  `null` explícito em campo NOT NULL
@pytest.mark.parametrize("campo", ["sku", "name"])
def test_produto_put_com_null_retorna_400(api, campo):
    produto = api.product()
    assert api.put(f"/products/{produto['id']}", {campo: None}).status_code == 400
    assert api.get(f"/products/{produto['id']}").json()[campo] == produto[campo]


@pytest.mark.parametrize("corpo", [{"sku": ""}, {"sku": "   "}, {"name": ""}])
def test_produto_com_texto_vazio_retorna_400(api, corpo):
    assert api.post("/products/", {"sku": "OK-1", "name": "Ok", **corpo}).status_code == 400
    produto = api.product()
    assert api.put(f"/products/{produto['id']}", corpo).status_code == 400


@pytest.mark.parametrize("corpo", [{"weight": -1}, {"volume": -0.5}])
def test_produto_com_peso_ou_volume_negativo_retorna_400(api, corpo):
    assert api.post("/products/", {"sku": "NEG-1", "name": "Neg", **corpo}).status_code == 400


def test_posicao_put_com_code_null_ou_longo_retorna_400(api):
    posicao = api.location(api.warehouse()["id"])
    assert api.put(f"/locations/{posicao['id']}", {"code": None}).status_code == 400
    assert api.put(f"/locations/{posicao['id']}", {"code": "X" * 21}).status_code == 400
    assert api.put(f"/locations/{posicao['id']}", {"aisle": "Y" * 11}).status_code == 400
    assert api.post("/locations", {"warehouse_id": posicao["warehouse_id"], "code": ""}).status_code == 400


@pytest.mark.parametrize("campo", ["status", "type"])
def test_tarefa_e_pedido_put_com_null_retorna_400(api, campo):
    pedido = api.order([{"product_id": api.product()["id"], "quantity": 1}])
    tarefa = api.task(pedido["id"])
    assert api.put(f"/orders/{pedido['id']}", {campo: None}).status_code == 400
    assert api.put(f"/tasks/{tarefa['id']}", {campo: None}).status_code == 400


def test_valores_de_enum_invalidos_retornam_400(api):
    produto = api.product()
    assert api.post("/orders/", {"type": "XYZ", "items": [{"product_id": produto["id"], "quantity": 1}]}).status_code == 400
    pedido = api.order([{"product_id": produto["id"], "quantity": 1}])
    assert api.put(f"/orders/{pedido['id']}", {"status": "FINALIZADO"}).status_code == 400
    assert api.get("/orders/", params={"type": "XYZ"}).status_code == 400
    assert api.get("/orders/", params={"status": "XYZ"}).status_code == 400
    assert api.get("/tasks/", params={"status": "XYZ"}).status_code == 400
    assert api.get("/tasks/", params={"type": "XYZ"}).status_code == 400


#  consistência de itens
def test_itens_repetidos_na_criacao_do_pedido_sao_somados(api):
    produto = api.product()
    pedido = api.order([
        {"product_id": produto["id"], "quantity": 2},
        {"product_id": produto["id"], "quantity": 3},
    ])
    assert len(pedido["items"]) == 1
    assert pedido["items"][0]["quantity"] == 5


#  referências inexistentes
def test_referencias_inexistentes_retornam_404_sem_deixar_lixo(api):
    produto = api.product()
    posicao = api.location(api.warehouse()["id"])
    assert api.post("/stock", {"product_id": 9999, "location_id": posicao["id"], "quantity": 1}).status_code == 404
    assert api.post("/stock", {"product_id": produto["id"], "location_id": 9999, "quantity": 1}).status_code == 404
    assert api.post("/locations", {"warehouse_id": 9999, "code": "Z-1"}).status_code == 404

    resp = api.post("/orders/", {"type": "OUTBOUND", "items": [
        {"product_id": produto["id"], "quantity": 1}, {"product_id": 9999, "quantity": 1}]})
    assert resp.status_code == 404
    assert api.get("/orders/").json() == []  # pedido não pode ficar órfão

    assert api.post("/tasks/", {"type": "PICKING", "order_id": 9999}).status_code == 404
    pedido = api.order([{"product_id": produto["id"], "quantity": 1}])
    assert api.post("/tasks/", {"type": "PICKING", "order_id": pedido["id"], "assigned_user_id": 9999}).status_code == 404


@pytest.mark.parametrize("url", ["/products/9999", "/orders/9999", "/tasks/9999", "/stock/9999", "/locations/9999", "/locations/warehouses/9999"])
def test_get_put_delete_de_id_inexistente_retornam_404(api, url):
    assert api.get(url).status_code == 404
    assert api.put(url, {"name": "x", "quantity": 1, "status": "PENDING", "code": "x"}).status_code in (400, 404)
    assert api.delete(url).status_code == 404


#  permissões nas regras de CRUD
def test_operador_nao_cria_produto_nem_exclui_pedido(api):
    assert api.post("/products/", {"sku": "OP-1", "name": "x"}, who="operador").status_code == 403
    pedido = api.order([{"product_id": api.product()["id"], "quantity": 1}])
    assert api.delete(f"/orders/{pedido['id']}", who="operador").status_code == 403