"""Constraints do banco: o banco recusa dados inválidos mesmo que a API falhe.

Insere direto com SQL (sem passar pela API) e espera IntegrityError.
Roda em SQLite (FKs ligadas) e no PostgreSQL via TEST_DATABASE_URL.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.crud_support import Session, api 


@pytest.fixture
def base(api):
    """Um produto, uma posição, um pedido e um item já criados pela API."""
    produto = api.product()
    posicao = api.location(api.warehouse()["id"])
    pedido = api.order([{"product_id": produto["id"], "quantity": 2}])
    return {"produto": produto["id"], "posicao": posicao["id"], "pedido": pedido["id"]}


def _executa(sql: str, **params):
    db = Session()
    try:
        db.execute(text(sql), params)
        db.commit()
    finally:
        db.close()


def test_estoque_negativo_e_recusado(base):
    with pytest.raises(IntegrityError):
        _executa("INSERT INTO stock (product_id, location_id, quantity) VALUES (:p, :l, -1)",
                 p=base["produto"], l=base["posicao"])


def test_item_de_pedido_com_quantidade_zero_e_recusado(base):
    with pytest.raises(IntegrityError):
        _executa("INSERT INTO order_items (order_id, product_id, quantity) VALUES (:o, :p, 0)",
                 o=base["pedido"], p=base["produto"])


@pytest.mark.parametrize("tabela,coluna,valor", [
    ("orders", "type", "TRANSFER"),
    ("orders", "status", "FINALIZADO"),
])
def test_pedido_com_tipo_ou_status_invalido_e_recusado(base, tabela, coluna, valor):
    campos = {"type": "OUTBOUND", "status": "PENDING", coluna: valor}
    with pytest.raises(IntegrityError):
        _executa("INSERT INTO orders (type, status) VALUES (:t, :s)", t=campos["type"], s=campos["status"])


@pytest.mark.parametrize("coluna,valor", [("type", "DELIVERY"), ("status", "DONE")])
def test_tarefa_com_tipo_ou_status_invalido_e_recusada(base, coluna, valor):
    campos = {"type": "PICKING", "status": "PENDING", coluna: valor}
    with pytest.raises(IntegrityError):
        _executa("INSERT INTO tasks (type, status, order_id) VALUES (:t, :s, :o)",
                 t=campos["type"], s=campos["status"], o=base["pedido"])


@pytest.mark.parametrize("coluna", ["weight", "volume"])
def test_produto_com_peso_ou_volume_negativo_e_recusado(base, coluna):
    with pytest.raises(IntegrityError):
        _executa(f"INSERT INTO products (sku, name, {coluna}) VALUES ('NEG', 'Neg', -1)")


def test_estoque_duplicado_por_produto_e_posicao_e_recusado(base):
    sql = "INSERT INTO stock (product_id, location_id, quantity) VALUES (:p, :l, 1)"
    _executa(sql, p=base["produto"], l=base["posicao"])
    with pytest.raises(IntegrityError):
        _executa(sql, p=base["produto"], l=base["posicao"])


def test_sku_duplicado_no_banco_e_recusado(base):
    with pytest.raises(IntegrityError):
        _executa("INSERT INTO products (sku, name) VALUES ('SKU-1', 'Outro')")


def test_produto_em_pedido_nao_pode_ser_excluido_direto_no_banco(base):
    """ON DELETE RESTRICT em order_items.product_id."""
    with pytest.raises(IntegrityError):
        _executa("DELETE FROM products WHERE id = :p", p=base["produto"])


def test_excluir_pedido_remove_itens_em_cascata(base):
    _executa("DELETE FROM orders WHERE id = :o", o=base["pedido"])
    db = Session()
    try:
        assert db.execute(text("SELECT count(*) FROM order_items")).scalar() == 0
    finally:
        db.close()


def test_fk_nula_e_recusada(base):
    with pytest.raises(IntegrityError):
        _executa("INSERT INTO stock (product_id, location_id, quantity) VALUES (NULL, :l, 1)", l=base["posicao"])
    with pytest.raises(IntegrityError):
        _executa("INSERT INTO tasks (type, status, order_id) VALUES ('PICKING', 'PENDING', NULL)")