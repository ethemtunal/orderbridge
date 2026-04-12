from orderbridge.common.types.order import (
    ProcessOrderEventData,
    ProcessOrderMessageBody,
)

TEST_TOPIC = "test.order.process"


def test_publish_and_receive_process_order(rabbitmq_client):
    event_data = ProcessOrderEventData(
        user_uuid="user-uuid-123",
        order_uuid="order-uuid-456",
        attempt=0,
    )

    rabbitmq_client.publish_process_order(event_data)

    message = rabbitmq_client.receive_message(TEST_TOPIC if False else "order.process")
    assert message is not None

    body = ProcessOrderMessageBody.model_validate(message.body)
    assert body.event_data.order_uuid == "order-uuid-456"
    assert body.event_data.user_uuid == "user-uuid-123"
    assert body.event_data.attempt == 0

    rabbitmq_client.delete_message("order.process", message.handle)


def test_receive_returns_none_on_empty_queue(rabbitmq_client):
    message = rabbitmq_client.receive_message(TEST_TOPIC)
    assert message is None


def test_delete_message_acks(rabbitmq_client):
    event_data = ProcessOrderEventData(
        user_uuid="user-uuid-789",
        order_uuid="order-uuid-101",
        attempt=1,
    )
    rabbitmq_client.publish_process_order(event_data)

    message = rabbitmq_client.receive_message("order.process")
    assert message is not None

    rabbitmq_client.delete_message("order.process", message.handle)

    # message should be gone after ack
    followup = rabbitmq_client.receive_message("order.process")
    assert followup is None


def test_republish_message(rabbitmq_client):
    rabbitmq_client.republish_message(
        topic=TEST_TOPIC,
        event_type="process_order",
        event_data={"order_uuid": "order-uuid-999"},
    )

    message = rabbitmq_client.receive_message(TEST_TOPIC)
    assert message is not None
    assert message.body["event_data"]["order_uuid"] == "order-uuid-999"
    rabbitmq_client.delete_message(TEST_TOPIC, message.handle)
