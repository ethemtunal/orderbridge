from orderbridge.adapters.database import models
from orderbridge.adapters.database.repositories.base_repository import BaseRepo
from orderbridge.common.exceptions import NotFound
from orderbridge.common.types import OrderEntity, OrderWithUser
from orderbridge.common.types.order import OrderStatus


class DBOrderRepo(BaseRepo):
    def insert(self, values: OrderWithUser) -> OrderEntity:
        order = models.Order.from_entity(values)
        self.session.add(order)
        self.session.flush()
        self.session.refresh(order)
        return order.to_entity()

    def get_by_id(self, id: int) -> OrderEntity:
        row = self.session.get(models.Order, id)
        if row is None:
            raise NotFound("No such order")
        return row.to_entity()

    def get_by_uuid(self, uuid: str) -> OrderEntity:
        row = self.session.query(models.Order).filter_by(uuid=uuid).one_or_none()
        if row is None:
            raise NotFound("No such order")
        return row.to_entity()

    def get_by_user(self, user_id: int) -> list[OrderEntity]:
        rows = self.session.query(models.Order).filter_by(user_id=user_id).all()
        return [row.to_entity() for row in rows]

    def update_status(self, uuid: str, status: OrderStatus) -> OrderEntity:
        row = self.session.query(models.Order).filter_by(uuid=uuid).one_or_none()
        if row is None:
            raise NotFound("No such order")
        row.status = status
        self.session.flush()
        self.session.refresh(row)
        return row.to_entity()
