# custom datetime.datetime annotation that allows custom serialization.
# removes TimeZone & microsecond info
# 2023-10-13T07:08:49.030000+00:00 >> 2023-10-13Z07:08:49
from datetime import datetime
from typing import Annotated

from pydantic.functional_serializers import PlainSerializer

from orderbridge.common.finance import Money

SerializedDatetime = Annotated[
    datetime,
    PlainSerializer(
        lambda x: x.replace(tzinfo=None).replace(microsecond=0).isoformat(),
        return_type=str,
    ),
]

# custom Money annotation that allows custom serialization.
SerializedMoney = Annotated[
    Money,
    PlainSerializer(
        lambda x: {"amount": float(x.amount), "currency": x.currency.code},
        return_type=dict,
    ),
]
