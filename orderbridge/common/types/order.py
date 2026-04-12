from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from orderbridge.common.types.serialized import SerializedMoney


class OrderStatus(StrEnum):
    PENDING = "pending"
    FAILED = "failed"
    PLACED = "placed"


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"


class OrderCreate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_id: int
    instrument: str
    type: OrderType
    side: OrderSide
    quantity: int
    limit_price: SerializedMoney | None
    status: OrderStatus
    retry_count: int

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("quantity must be greater than 0")
        return v

    @field_validator("limit_price")
    @classmethod
    def limit_price_must_be_positive(
        cls, v: SerializedMoney | None
    ) -> SerializedMoney | None:
        if v is not None and v.amount <= 0:
            raise ValueError("limit_price must be greater than 0")
        return v

    @model_validator(mode="after")
    def validate_limit_price_for_order_type(self) -> "OrderCreate":
        if self.type == OrderType.MARKET and self.limit_price is not None:
            raise ValueError("limit_price must be None for market orders")
        if self.type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        return self


class OrderEntity(OrderCreate):
    model_config = ConfigDict(arbitrary_types_allowed=True, from_attributes=True)

    id: int
    uuid: str
    created_at: datetime
    updated_at: datetime
