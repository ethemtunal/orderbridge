import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from orderbridge.adapters.database.models.base import Base
from orderbridge.adapters.database.models.user import User
from orderbridge.common.types import (
    OrderEntity,
    OrderSide,
    OrderStatus,
    OrderType,
    OrderWithUser,
)
from orderbridge.common.utils import money_or_none


class Order(Base):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    instrument: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    limit_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    currency: Mapped[str | None] = mapped_column(String, nullable=True, default="EUR")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="orders")

    __table_args__ = (
        CheckConstraint(
            "(type = 'market' AND limit_price IS NULL) OR (type = 'limit' AND limit_price IS NOT NULL)",
            name="ck_order_limit_price",
        ),
        CheckConstraint("quantity > 0", name="ck_order_quantity_positive"),
        CheckConstraint("limit_price > 0", name="ck_order_limit_price_positive"),
    )

    def to_entity(self) -> OrderEntity:
        return OrderEntity(
            id=self.id,
            uuid=self.uuid,
            user_id=self.user_id,
            instrument=self.instrument,
            type=OrderType(self.type),
            side=OrderSide(self.side),
            quantity=self.quantity,
            limit_price=money_or_none(self.limit_price, self.currency),
            status=OrderStatus(self.status),
            retry_count=self.retry_count,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, order: OrderWithUser) -> "Order":
        return cls(
            user_id=order.user_id,
            instrument=order.instrument,
            type=order.type,
            side=order.side,
            quantity=order.quantity,
            limit_price=(
                order.limit_price.amount_in_mill
                if order.limit_price is not None
                else None
            ),
            status=order.status,
            currency=(
                order.limit_price.currency if order.limit_price is not None else None
            ),
            retry_count=order.retry_count,
        )
