from abc import ABC

from sqlalchemy.orm import Session


class BaseRepo(ABC):
    def __init__(
        self,
        session: Session,
    ):
        self.session = session
