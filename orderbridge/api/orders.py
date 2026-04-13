import logging

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, model_validator
from sqlalchemy.orm import Session

from orderbridge.api.dependencies import get_db
from orderbridge.common.types import OrderCreate, OrderEntity
from orderbridge.common.types.order import OrderSide, OrderStatus, OrderType
from orderbridge.common.types.serialized import SerializedMoney
from orderbridge.services.order_service import get_order_service

logger = logging.getLogger(__name__)

router = APIRouter()


class OrderRequest(BaseModel):
    instrument: str
    type: OrderType
    side: OrderSide
    quantity: int
    limit_price: float | None = None
    currency: str = "EUR"

    @model_validator(mode="after")
    def validate_limit_price_for_type(self) -> "OrderRequest":
        if self.type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        if self.type == OrderType.MARKET and self.limit_price is not None:
            raise ValueError("limit_price must be None for market orders")
        return self

    def to_order_create(self) -> OrderCreate:
        limit_price = (
            SerializedMoney(self.limit_price, self.currency)
            if self.limit_price is not None
            else None
        )
        return OrderCreate(
            instrument=self.instrument,
            type=self.type,
            side=self.side,
            quantity=self.quantity,
            limit_price=limit_price,
            status=OrderStatus.PENDING,
        )


@router.get("/orders", response_model=list[OrderEntity])
def get_orders(
    x_user_uuid: str = Header(...),
    db: Session = Depends(get_db),
) -> list[OrderEntity]:
    try:
        service = get_order_service(db)
        return service.get_orders_by_user(x_user_uuid)
    except Exception:
        logger.exception("Error fetching orders")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching orders",
        )


@router.post("/orders", status_code=201, response_model=OrderEntity)
def create_order(
    order: OrderRequest,
    x_user_uuid: str = Header(...),
    db: Session = Depends(get_db),
) -> OrderEntity | JSONResponse:
    try:
        service = get_order_service(db)
        db_order = service.create_order(x_user_uuid, order.to_order_create())
        service.place_order_with_retry(db_order.uuid)
        return db_order
    except Exception:
        logger.exception("Error creating order")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error while placing the order"},
        )
