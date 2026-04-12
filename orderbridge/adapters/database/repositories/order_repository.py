from orderbridge.adapters.database import models
from orderbridge.adapters.database.repositories.base_repository import BaseRepo
from orderbridge.common.exceptions import NotFound
from orderbridge.common.types import OrderCreate, OrderEntity


class DBOrderRepo(BaseRepo):
    def insert(self, values: OrderCreate) -> OrderEntity:
        order = models.Order(**values.model_dump())
        self.session.add(order)
        self.session.flush()
        self.session.refresh(order)
        return OrderEntity.model_validate(order)

    def get_by_id(self, id: int) -> OrderEntity:
        row = self.session.get(models.Order, id)
        if row is None:
            raise NotFound("No such order")
        return OrderEntity.model_validate(row)

    def get_by_uuid(self, uuid: str) -> OrderEntity:
        row = self.session.query(models.Order).filter_by(uuid=uuid).one_or_none()
        if row is None:
            raise NotFound("No such order")
        return OrderEntity.model_validate(row)

    def get_by_user(self, user_id: int) -> list[OrderEntity]:
        rows = self.session.query(models.Order).filter_by(user_id=user_id).all()
        return [models.Order.to_entity(row) for row in rows]
