import pytest

from orderbridge.adapters.database.repositories import DBOrderRepo, DBUserRepo
from orderbridge.adapters.queues.rabbitmq_queue_client import PROCESS_ORDER_TOPIC
from orderbridge.common.datagen.user_factory import UserFactory
from orderbridge.common.exceptions import NotFound
from orderbridge.common.types.order import (
    OrderCreate,
    OrderSide,
    OrderStatus,
    OrderType,
    ProcessOrderMessageBody,
)
from orderbridge.services.order_service import OrderService


@pytest.fixture
def order_service(orderbridge_db, rabbitmq_client):
    return OrderService(
        user_repository=DBUserRepo(orderbridge_db),
        order_repository=DBOrderRepo(orderbridge_db),
        queue_client=rabbitmq_client,
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


def test_create_order_publishes_to_queue(order_service, rabbitmq_client):
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

    message = rabbitmq_client.receive_message(PROCESS_ORDER_TOPIC)
    assert message is not None

    body = ProcessOrderMessageBody.model_validate(message.body)
    assert body.event_data.order_uuid == result.uuid
    assert body.event_data.user_uuid == user.uuid

    rabbitmq_client.delete_message(PROCESS_ORDER_TOPIC, message.handle)


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
