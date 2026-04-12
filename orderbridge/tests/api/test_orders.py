from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from orderbridge.api.dependencies import get_db
from orderbridge.common.datagen.user_factory import UserFactory
from orderbridge.common.types.order import OrderStatus
from orderbridge.main import app


@pytest.fixture
def client(orderbridge_db):
    app.dependency_overrides[get_db] = lambda: orderbridge_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def order_payload(**overrides):
    return {
        "instrument": "DE000A0Q4RZ3",
        "type": "limit",
        "side": "buy",
        "quantity": 10,
        "limit_price": 123.32,
        "status": "pending",
        "retry_count": 0,
        "currency": "EUR",
        **overrides,
    }


@patch("orderbridge.services.order_service.place_order")
def test_create_order_returns_201(mock_place, client):
    user = UserFactory.create()

    response = client.post(
        "/orders",
        json=order_payload(),
        headers={"x-user-uuid": user.uuid},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["instrument"] == "DE000A0Q4RZ3"
    assert data["status"] == OrderStatus.PENDING
    assert data["user_id"] == user.id


@patch("orderbridge.services.order_service.place_order")
def test_create_order_returns_500_if_user_not_found(mock_place, client):
    response = client.post(
        "/orders",
        json=order_payload(),
        headers={"x-user-uuid": "non-existent-uuid"},
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Internal server error while placing the order"
    }


def test_create_order_returns_422_if_invalid_payload(client):
    user = UserFactory.create()

    response = client.post(
        "/orders",
        json={"instrument": "DE000A0Q4RZ3"},
        headers={"x-user-uuid": user.uuid},
    )

    assert response.status_code == 422


def test_create_order_returns_422_if_missing_user_header(client):
    response = client.post("/orders", json=order_payload())

    assert response.status_code == 422


@patch("orderbridge.services.order_service.place_order")
def test_create_order_returns_422_for_invalid_order_type(mock_place, client):
    user = UserFactory.create()

    response = client.post(
        "/orders",
        json=order_payload(type="invalid"),
        headers={"x-user-uuid": user.uuid},
    )

    assert response.status_code == 422
