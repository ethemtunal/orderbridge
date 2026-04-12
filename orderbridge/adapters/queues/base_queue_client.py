import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from orderbridge.common.types.order import (
    ProcessOrderEventData,
)

logger = logging.getLogger(__name__)


@dataclass
class Message:
    body: dict | str | None
    handle: str


class QueuingClient(ABC):
    @abstractmethod
    def republish_message(
        self, topic: str, event_type: str, event_data: dict[str, Any]
    ) -> None: ...

    @abstractmethod
    def publish_process_order(
        self, process_order_event_data: ProcessOrderEventData
    ) -> None: ...

    @abstractmethod
    def receive_message(
        self,
        topic: str,
        timeout: float | None = None,
        visibility_timeout: int | None = None,
    ) -> Message | None: ...

    @abstractmethod
    def receive_messages(
        self,
        topic: str,
        max_number: int = 10,
        timeout: float | None = None,
        visibility_timeout: int | None = None,
    ) -> list[Message]: ...

    @abstractmethod
    def delete_message(self, topic: str, receipt_handle: str) -> None: ...
