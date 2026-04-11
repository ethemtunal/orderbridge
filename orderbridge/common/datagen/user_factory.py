import uuid
from datetime import datetime

import factory
from factory.alchemy import SQLAlchemyModelFactory

from orderbridge.adapters.database.models.user import User
from orderbridge.tests.conftest import get_session_factory


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_factory = get_session_factory
        sqlalchemy_session_persistence = "flush"

    name = factory.Sequence(lambda n: f"User {n}")
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))
