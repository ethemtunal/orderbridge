import logging

from sqlalchemy.orm import Session

from orderbridge.adapters.database.repositories import DBOrderRepo, DBUserRepo
from orderbridge.adapters.queues.base_queue_client import QueuingClient
from orderbridge.adapters.queues.rabbitmq_queue_client import RabbitMQQueueClient
from orderbridge.common.types import (
    OrderCreate,
    OrderEntity,
    OrderStatus,
    OrderWithUser,
)
from orderbridge.common.types.order import (
    ProcessOrderEventData,
)

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(
        self,
        user_repository: DBUserRepo,
        order_repository: DBOrderRepo,
        queue_client: QueuingClient,
    ):
        self.user_repository = user_repository
        self.order_repository = order_repository
        self.queue_client = queue_client

    def create_order(self, user_uuid: str, order: OrderCreate) -> OrderEntity:
        user = self.user_repository.get_by_uuid(user_uuid)
        if order.status != OrderStatus.PENDING:
            logger.info(f"Changing order status to {OrderStatus.PENDING}")
            order.status = OrderStatus.PENDING
        db_order = self.order_repository.insert(
            OrderWithUser(user_id=user.id, **order.model_dump())
        )
        logger.info(f"Order {db_order.uuid} created for user {user_uuid}")
        self.queue_client.publish_process_order(
            ProcessOrderEventData(
                user_uuid=user.uuid,
                order_uuid=db_order.uuid,
                attempt=1,
            )
        )
        return db_order


def get_order_service(db_session: Session) -> OrderService:
    return OrderService(
        user_repository=DBUserRepo(db_session),
        order_repository=DBOrderRepo(db_session),
        queue_client=RabbitMQQueueClient(
            "localhost",
            5673,
            "orderbridge",
            "rabbitpasswd",
        ),
    )
