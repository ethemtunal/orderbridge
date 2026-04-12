from unittest.mock import patch

import pytest

from orderbridge.adapters.database.repositories import DBOrderRepo, DBUserRepo
from orderbridge.common.datagen.order_factory import OrderFactory
from orderbridge.common.datagen.user_factory import UserFactory
from orderbridge.common.exceptions import NotFound, OrderPlacementError
from orderbridge.common.types.order import (
    OrderCreate,
    OrderSide,
    OrderStatus,
    OrderType,
)
from orderbridge.services.order_service import MAX_RETRIES, OrderService


@pytest.fixture
def order_service(orderbridge_db) -> OrderService:
    return OrderService(
        user_repository=DBUserRepo(orderbridge_db),
        order_repository=DBOrderRepo(orderbridge_db),
    )


def test_create_order_returns_order_entity(order_service):
    user = UserFactory.create()
    order_create = OrderCreate(
        instrument="DE000A0Q4RZ3",
        type=OrderType.MARKET,
        side=OrderSide.BUY,
        quantity=10,
        limit_price=None,
        status=OrderStatus.PENDING,
        retry_count=0,
    )

    result = order_service.create_order(user.uuid, order_create)

    assert result.instrument == "DE000A0Q4RZ3"
    assert result.user_id == user.id
    assert result.status == OrderStatus.PENDING


def test_create_order_with_failed_status(order_service):
    user = UserFactory.create()
    order_create = OrderCreate(
        instrument="DE000A0Q4RZ3",
        type=OrderType.MARKET,
        side=OrderSide.BUY,
        quantity=10,
        limit_price=None,
        status=OrderStatus.FAILED,
        retry_count=0,
    )

    result = order_service.create_order(user.uuid, order_create)

    assert result.instrument == "DE000A0Q4RZ3"
    assert result.user_id == user.id
    assert result.status == OrderStatus.PENDING


def test_create_order_raises_if_user_not_found(order_service):
    order_create = OrderCreate(
        instrument="DE000A0Q4RZ3",
        type=OrderType.MARKET,
        side=OrderSide.BUY,
        quantity=10,
        limit_price=None,
        status=OrderStatus.PENDING,
        retry_count=0,
    )

    with pytest.raises(NotFound):
        order_service.create_order("non-existent-uuid", order_create)


@patch("orderbridge.services.order_service.time.sleep")
@patch("orderbridge.services.order_service.place_order")
def test_place_order_with_retry_places_on_first_success(
    mock_place, mock_sleep, order_service, orderbridge_db
):
    order = OrderFactory.create()

    order_service.place_order_with_retry(order.uuid)

    mock_place.assert_called_once_with(order.uuid)
    mock_sleep.assert_not_called()
    updated = orderbridge_db.get(type(order), order.id)
    assert updated.status == OrderStatus.PLACED


@patch("orderbridge.services.order_service.time.sleep")
@patch("orderbridge.services.order_service.place_order")
def test_place_order_with_retry_retries_on_failure(
    mock_place, mock_sleep, order_service, orderbridge_db
):
    order = OrderFactory.create()
    mock_place.side_effect = [OrderPlacementError("fail"), None]

    order_service.place_order_with_retry(order.uuid)

    assert mock_place.call_count == 2
    mock_sleep.assert_called_once()
    updated = orderbridge_db.get(type(order), order.id)
    assert updated.status == OrderStatus.PLACED


@patch("orderbridge.services.order_service.time.sleep")
@patch("orderbridge.services.order_service.place_order")
def test_place_order_with_retry_marks_failed_after_max_retries(
    mock_place, mock_sleep, order_service, orderbridge_db
):
    order = OrderFactory.create()
    mock_place.side_effect = OrderPlacementError("fail")

    order_service.place_order_with_retry(order.uuid)

    assert mock_place.call_count == MAX_RETRIES
    updated = orderbridge_db.get(type(order), order.id)
    assert updated.status == OrderStatus.FAILED
