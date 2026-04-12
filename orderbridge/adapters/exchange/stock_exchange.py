import random
import time

from orderbridge.common.exceptions import OrderPlacementError


def place_order(order_uuid: str) -> None:
    if random.random() < 0.1:
        raise OrderPlacementError("Failed to place order at stock exchange")
    time.sleep(0.5)
