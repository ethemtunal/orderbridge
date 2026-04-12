import pytest
from pydantic import ValidationError

from orderbridge.common.finance import Money
from orderbridge.common.types.order import (
    OrderCreate,
    OrderSide,
    OrderStatus,
    OrderType,
)


def valid_market_order(**overrides):
    return {
        "user_id": 1,
        "instrument": "DE000A0Q4RZ3",
        "type": OrderType.MARKET,
        "side": OrderSide.BUY,
        "quantity": 10,
        "limit_price": None,
        "status": OrderStatus.PENDING,
        **overrides,
    }


def valid_limit_order(**overrides):
    return {
        "user_id": 1,
        "instrument": "DE000A0Q4RZ3",
        "type": OrderType.LIMIT,
        "side": OrderSide.BUY,
        "quantity": 10,
        "limit_price": Money(100, "EUR"),
        "status": OrderStatus.PENDING,
        **overrides,
    }


def test_valid_market_order():
    order = OrderCreate(**valid_market_order())
    assert order.type == OrderType.MARKET
    assert order.limit_price is None


def test_valid_limit_order():
    order = OrderCreate(**valid_limit_order())
    assert order.type == OrderType.LIMIT
    assert order.limit_price is not None


def test_quantity_must_be_positive():
    with pytest.raises(ValidationError, match="quantity must be greater than 0"):
        OrderCreate(**valid_market_order(quantity=0))


def test_quantity_cannot_be_negative():
    with pytest.raises(ValidationError, match="quantity must be greater than 0"):
        OrderCreate(**valid_market_order(quantity=-1))


def test_market_order_cannot_have_limit_price():
    with pytest.raises(
        ValidationError, match="limit_price must be None for market orders"
    ):
        OrderCreate(**valid_market_order(limit_price=Money(100, "EUR")))


def test_limit_order_requires_limit_price():
    with pytest.raises(
        ValidationError, match="limit_price is required for limit orders"
    ):
        OrderCreate(**valid_limit_order(limit_price=None))


def test_limit_price_must_be_positive():
    with pytest.raises(ValidationError, match="limit_price must be greater than 0"):
        OrderCreate(**valid_limit_order(limit_price=Money(-1, "EUR")))


def test_invalid_side():
    with pytest.raises(ValidationError):
        OrderCreate(**valid_market_order(side="invalid"))


def test_invalid_type():
    with pytest.raises(ValidationError):
        OrderCreate(**valid_market_order(type="invalid"))
