import pytest

from orderbridge.adapters.database.repositories import DBOrderRepo
from orderbridge.common.datagen.order_factory import OrderFactory
from orderbridge.common.datagen.user_factory import UserFactory
from orderbridge.common.exceptions import NotFound
from orderbridge.common.types.order import OrderStatus


def test_get_order_by_id(orderbridge_db):
    order = OrderFactory.create()
    order_repo = DBOrderRepo(orderbridge_db)
    fetched = order_repo.get_by_id(order.id)
    assert fetched.id == order.id


def test_get_order_by_uuid(orderbridge_db):
    order = OrderFactory.create()
    order_repo = DBOrderRepo(orderbridge_db)
    fetched = order_repo.get_by_uuid(order.uuid)
    assert fetched.id == order.id


def test_get_orders_by_user(orderbridge_db):
    user = UserFactory.create()
    OrderFactory.create(user=user)
    OrderFactory.create(user=user)
    order_repo = DBOrderRepo(orderbridge_db)
    orders = order_repo.get_by_user(user.id)
    assert len(orders) == 2
    assert all(o.user_id == user.id for o in orders)


def test_get_order_by_id_not_found(orderbridge_db):
    order_repo = DBOrderRepo(orderbridge_db)
    with pytest.raises(NotFound):
        order_repo.get_by_id(999999)


def test_get_order_by_uuid_not_found(orderbridge_db):
    order_repo = DBOrderRepo(orderbridge_db)
    with pytest.raises(NotFound):
        order_repo.get_by_uuid("non-existent-uuid")


def test_get_orders_by_user_returns_empty(orderbridge_db):
    order_repo = DBOrderRepo(orderbridge_db)
    orders = order_repo.get_by_user(999999)
    assert orders == []


def test_update_status(orderbridge_db):
    order = OrderFactory.create(status=OrderStatus.FAILED)
    order_repo = DBOrderRepo(orderbridge_db)
    order_repo.update_status(order.uuid, OrderStatus.PLACED)
    fetched = order_repo.get_by_uuid(order.uuid)
    assert fetched.status == OrderStatus.PLACED
