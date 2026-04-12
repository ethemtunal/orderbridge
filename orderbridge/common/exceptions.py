from http import HTTPStatus


class OrderBridgeException(Exception):
    """Base class for all OrderBridge exceptions."""

    message: str
    status_code: int = 500

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFound(OrderBridgeException):
    status_code = HTTPStatus.NOT_FOUND


class OrderPlacementError(OrderBridgeException):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
