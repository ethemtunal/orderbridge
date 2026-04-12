import json
import time
import uuid

import pika
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection
from pika.exceptions import AMQPChannelError, AMQPConnectionError

from orderbridge.adapters.queues.base_queue_client import Message, QueuingClient
from orderbridge.common.types.order import (
    ProcessOrderEventData,
    ProcessOrderMessageBody,
)

PROCESS_ORDER_TOPIC = "order.process"


class RabbitMQQueueClient(QueuingClient):
    def __init__(
        self, host: str, port: int, username: str, password: str, vhost: str = "/"
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        self.credentials = pika.PlainCredentials(username, password)
        self.connection_params = pika.ConnectionParameters(
            host=host,
            port=port,
            virtual_host=vhost,
            credentials=self.credentials,
            heartbeat=600,
            blocked_connection_timeout=300,
        )

        self._connection: BlockingConnection | None = None
        self._channel: BlockingChannel | None = None
        self._unacked: dict[str, int] = {}
        self._connect()

    def _connect(self) -> None:
        try:
            if self._connection and not self._connection.is_closed:
                self._connection.close()
            self._connection = pika.BlockingConnection(self.connection_params)
            self._channel = self._connection.channel()
            self._channel.basic_qos(prefetch_count=1)
            self._unacked.clear()
        except AMQPConnectionError as e:
            raise ConnectionError(f"Failed to connect to RabbitMQ: {e}")

    def _ensure_connection(self) -> None:
        if not self._connection or self._connection.is_closed:
            self._connect()
        elif not self._channel or self._channel.is_closed:
            self._channel = self._connection.channel()
            self._channel.basic_qos(prefetch_count=1)

    def _declare_queue(self, topic: str) -> None:
        assert self._channel is not None
        self._channel.queue_declare(queue=topic, durable=True)

    def republish_message(self, topic: str, event_type: str, event_data: dict) -> None:
        self._ensure_connection()
        assert self._channel is not None
        self._declare_queue(topic)
        self._channel.basic_publish(
            exchange="",
            routing_key=topic,
            body=json.dumps({"event_type": event_type, "event_data": event_data}),
            properties=pika.BasicProperties(delivery_mode=2),
        )

    def publish_process_order(
        self, process_order_event_data: ProcessOrderEventData
    ) -> None:
        self._ensure_connection()
        assert self._channel is not None
        self._declare_queue(PROCESS_ORDER_TOPIC)
        body = ProcessOrderMessageBody(event_data=process_order_event_data)
        self._channel.basic_publish(
            exchange="",
            routing_key=PROCESS_ORDER_TOPIC,
            body=body.model_dump_json(),
            properties=pika.BasicProperties(delivery_mode=2),
        )

    def receive_message(
        self,
        topic: str,
        timeout: float | None = None,
        visibility_timeout: int | None = None,
    ) -> Message | None:
        messages = self.receive_messages(topic=topic, max_number=1, timeout=timeout)
        return messages[0] if messages else None

    def receive_messages(
        self,
        topic: str,
        max_number: int = 10,
        timeout: float | None = None,
        visibility_timeout: int | None = None,
    ) -> list[Message]:
        messages: list[Message] = []
        start_time = time.time()

        try:
            self._ensure_connection()
            self._declare_queue(topic)
            assert self._channel is not None

            while len(messages) < max_number:
                if timeout is not None and time.time() - start_time >= timeout:
                    break

                method, _, body = self._channel.basic_get(queue=topic, auto_ack=False)

                if method is None:
                    if timeout is not None and timeout > 0:
                        time.sleep(min(0.1, timeout - (time.time() - start_time)))
                        continue
                    else:
                        break

                handle = str(uuid.uuid4())
                self._unacked[handle] = method.delivery_tag

                try:
                    decoded = body.decode("utf-8") if body else None
                    message_body = json.loads(decoded) if decoded else None
                except (json.JSONDecodeError, Exception):
                    message_body = body

                messages.append(Message(body=message_body, handle=handle))

        except AMQPChannelError as e:
            raise RuntimeError(f"Failed to receive messages: {e}")

        return messages

    def purge_queue(self, topic: str) -> None:
        self._ensure_connection()
        self._declare_queue(topic)
        assert self._channel is not None
        self._channel.queue_purge(queue=topic)
        self._unacked.clear()

    def delete_message(self, topic: str, receipt_handle: str) -> None:
        delivery_tag = self._unacked.get(receipt_handle)
        if delivery_tag is None:
            raise RuntimeError(
                f"No tracked delivery_tag for receipt_handle: {receipt_handle}"
            )

        retries = 3
        last_exc: Exception | None = None
        for attempt in range(retries):
            try:
                self._ensure_connection()
                assert self._channel is not None
                self._channel.basic_ack(delivery_tag=delivery_tag)
                self._unacked.pop(receipt_handle, None)
                return
            except Exception as e:
                last_exc = e
            if attempt < retries - 1:
                time.sleep(0.5 * (2**attempt))
        raise RuntimeError(f"Failed to ack message: {last_exc}")


QUEUE_CLIENT: RabbitMQQueueClient | None = None


def get_rabbitmq_queue_client(
    host: str, port: int, username: str, password: str
) -> RabbitMQQueueClient:
    global QUEUE_CLIENT
    if QUEUE_CLIENT is not None:
        return QUEUE_CLIENT
    QUEUE_CLIENT = RabbitMQQueueClient(
        host=host, port=port, username=username, password=password
    )
    return QUEUE_CLIENT
