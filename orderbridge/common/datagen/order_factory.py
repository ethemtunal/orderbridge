import uuid
from datetime import datetime

import factory
from factory.alchemy import SQLAlchemyModelFactory

from orderbridge.adapters.database.models.order import Order
from orderbridge.common.datagen.user_factory import UserFactory
from orderbridge.common.types.order import OrderSide, OrderStatus, OrderType
from orderbridge.tests.conftest import get_session_factory


class OrderFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Order
        sqlalchemy_session_factory = get_session_factory
        sqlalchemy_session_persistence = "flush"

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.LazyAttribute(lambda _: UserFactory.create().id)
    instrument = factory.Faker("bothify", text="DE###########")
    type = OrderType.MARKET
    side = OrderSide.BUY
    quantity = factory.Faker("random_int", min=1, max=100)
    limit_price = None
    status = OrderStatus.PENDING
    currency = "EUR"
    retry_count = 0
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
