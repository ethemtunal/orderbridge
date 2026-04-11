import alembic.config  # pylint: disable=wrong-import-order
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    __abstract__ = True


def create_all(engine) -> None:
    Base.metadata.create_all(bind=engine)


def alembic_migrate() -> None:
    args = ["--raiseerr", "--name", "orderbridge", "upgrade", "head"]
    alembic.config.main(argv=args)
