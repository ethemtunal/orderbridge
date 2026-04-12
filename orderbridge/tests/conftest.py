from collections.abc import Generator
from contextlib import contextmanager

import pytest
import testing.postgresql  # type: ignore[import-untyped]
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from orderbridge.adapters.database import models
from orderbridge.adapters.queues.rabbitmq_queue_client import RabbitMQQueueClient

RABBITMQ_HOST = "localhost"
RABBITMQ_PORT = 5673
RABBITMQ_USER = "orderbridge"
RABBITMQ_PASS = "rabbitpasswd"

TEST_SESSION: Session | None = None


def get_db_engine():
    # create engine
    pg = testing.postgresql.Postgresql()
    engine = create_engine(pg.url(), pool_size=10, max_overflow=20)
    engine._pg = pg  # keep the server alive
    models.Base.metadata.create_all(engine)

    # create session maker
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    return engine, session


@contextmanager
def get_test_db_session() -> Generator[Session, None, None]:
    # get engine and session maker
    engine, SessionLocal = get_db_engine()

    # create a connection and begin a transaction
    connection = engine.connect()
    transaction = connection.begin()

    # create a session bound to this connection
    session = SessionLocal(bind=connection)

    # begin a nested transaction (SAVEPOINT)
    nested = connection.begin_nested()
    global TEST_SESSION
    TEST_SESSION = session
    try:
        yield session
    finally:
        TEST_SESSION = None
        session.close()
        if nested.is_active:
            nested.rollback()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def orderbridge_db():
    with get_test_db_session() as session:
        yield session


@pytest.fixture(scope="function")
def rabbitmq_client():
    client = RabbitMQQueueClient(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        username=RABBITMQ_USER,
        password=RABBITMQ_PASS,
    )
    yield client


def get_session_factory() -> Session:
    # check if there is an active test session
    if TEST_SESSION is not None:
        return TEST_SESSION

    # if not create and return
    engine, SessionLocal = get_db_engine()
    return SessionLocal()
