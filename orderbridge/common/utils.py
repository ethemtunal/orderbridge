from decimal import Decimal

from orderbridge.common.finance import MONEY_CONVERSION_FACTOR
from orderbridge.common.types import SerializedMoney


def money_or_none(amount: int | None, currency: str | None) -> SerializedMoney | None:
    if amount is None or currency is None:
        return None
    assert currency is not None
    return SerializedMoney(Decimal(amount) / MONEY_CONVERSION_FACTOR, currency=currency)
