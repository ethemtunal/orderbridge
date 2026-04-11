from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    uuid: str


class UserEntity(UserCreate):
    id: int
    created_at: datetime
    updated_at: datetime
