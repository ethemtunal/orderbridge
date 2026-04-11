from orderbridge.adapters.database import models
from orderbridge.adapters.database.repositories.base_repository import BaseRepo
from orderbridge.common.exceptions import NotFound
from orderbridge.common.types import UserCreate, UserEntity


class DBUserRepo(BaseRepo):
    def insert(self, values: UserCreate) -> UserEntity:
        user = models.User(**values.model_dump())
        self.session.add(user)
        self.session.flush()
        self.session.refresh(user)
        return UserEntity.model_validate(user)

    def get_by_id(self, id: int) -> UserEntity:
        row = self.session.get(models.User, id)
        if row is None:
            raise NotFound("No such user")
        return UserEntity.model_validate(row)

    def get_by_uuid(self, uuid: str) -> UserEntity:
        row = self.session.query(models.User).filter_by(uuid=uuid).one_or_none()
        if row is None:
            raise NotFound("No such user")
        return UserEntity.model_validate(row)
