import logging
import time

from sqlalchemy.orm import Session

from orderbridge.adapters.database.repositories import DBOrderRepo, DBUserRepo
from orderbridge.adapters.exchange.stock_exchange import place_order
from orderbridge.common.exceptions import OrderPlacementError
from orderbridge.common.types import OrderCreate, OrderEntity, OrderWithUser
from orderbridge.common.types.order import OrderStatus

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


class OrderService:
    def __init__(self, user_repository: DBUserRepo, order_repository: DBOrderRepo):
        self.user_repository = user_repository
        self.order_repository = order_repository

    def create_order(self, user_uuid: str, order: OrderCreate) -> OrderEntity:
        user = self.user_repository.get_by_uuid(user_uuid)
        if order.status != OrderStatus.PENDING:
            logger.info(f"Changing order status to {OrderStatus.PENDING}")
            order.status = OrderStatus.PENDING
        db_order = self.order_repository.insert(
            OrderWithUser.from_order_create(order=order, user_id=user.id)
        )
        logger.info(f"Order {db_order.uuid} created for user {user_uuid}")
        return db_order

    def get_orders_by_user(self, user_uuid: str) -> list[OrderEntity]:
        user = self.user_repository.get_by_uuid(user_uuid)
        return self.order_repository.get_by_user(user.id)

    def place_order_with_retry(self, order_uuid: str) -> None:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                place_order(order_uuid)
                self.order_repository.update_status(order_uuid, OrderStatus.PLACED)
                logger.info(f"Order {order_uuid} placed on attempt {attempt}")
                return
            except OrderPlacementError:
                logger.warning(f"Order {order_uuid} failed on attempt {attempt}")
                if attempt < MAX_RETRIES:
                    time.sleep(0.5)

        self.order_repository.update_status(order_uuid, OrderStatus.FAILED)
        logger.error(
            f"Order {order_uuid} permanently failed after {MAX_RETRIES} attempts"
        )
        raise OrderPlacementError(f"Order {order_uuid} cannot be placed")


def get_order_service(db_session: Session) -> OrderService:
    return OrderService(
        user_repository=DBUserRepo(db_session),
        order_repository=DBOrderRepo(db_session),
    )
