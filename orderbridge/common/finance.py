from moneyed import Money as WrappedMoney

PRECISION = 3
MONEY_FIELD_PRECISION = "{:.3f}"
MONEY_CONVERSION_FACTOR = 10**PRECISION


class Money(WrappedMoney):
    @property
    def amount_in_mill(self) -> int:
        return int(self.amount * MONEY_CONVERSION_FACTOR)
