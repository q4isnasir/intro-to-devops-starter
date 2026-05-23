"""Unit tests for FruitAPI handlers.

Uses FastAPI's TestClient and an in-memory FakeFruitStore — no real server,
no MySQL needed. Each test gets a fresh, empty fake store.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import FakeFruitStore, get_store

# TestClient wraps the FastAPI app and lets us send fake HTTP requests
# to it in-process. No uvicorn, no network — just function calls.
client = TestClient(app)


@pytest.fixture(autouse=True)
def fake_store():
    """
    Before each test: install a brand-new FakeFruitStore for the app to use.
    After each test: remove the override so we don't leak state between tests.
    """
    store = FakeFruitStore()
    app.dependency_overrides[get_store] = lambda: store
    yield store
    app.dependency_overrides.clear()


def seed_fruits():
    """Adds a known set of fruits via the API. Returns the list of responses."""
    fruits = [
        {"name": "apple", "price": 1.50, "in_season": True},
        {"name": "banana", "price": 0.75, "in_season": True},
        {"name": "cherry", "price": 3.00, "in_season": False},
    ]
    return [client.post("/fruits", json=f).json() for f in fruits]


# ---------- Positive: health ----------

def test_health_returns_ok():
    """GET /health should return 200 and {"status": "ok"}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------- Positive: response shape ----------

def test_post_returns_fruit_with_expected_fields():
    """POST /fruits returns JSON with id + the fields we sent + created_at."""
    payload = {"name": "mango", "price": 2.50, "in_season": True}
    response = client.post("/fruits", json=payload)

    assert response.status_code == 201
    body = response.json()

    # All expected keys present
    assert set(body.keys()) == {"id", "name", "price", "in_season", "created_at"}
    # Values we sent come back unchanged
    assert body["name"] == "mango"
    assert body["price"] == 2.50
    assert body["in_season"] is True
    # Server-assigned fields look right
    assert isinstance(body["id"], int)
    assert isinstance(body["created_at"], str)  # ISO timestamp as a string


# ---------- Positive: list fruits ----------

def test_list_fruits_returns_all_seeded():
    """GET /fruits returns 200 and the list we seeded."""
    seeded = seed_fruits()
    response = client.get("/fruits")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == len(seeded)
    # Names should match (order matters because we add sequentially)
    assert [f["name"] for f in body] == ["apple", "banana", "cherry"]


# ---------- Positive: cheapest fruit ----------

def test_cheapest_returns_lowest_price_fruit():
    """GET /fruits/cheapest returns the cheapest fruit (banana at 0.75)."""
    seed_fruits()
    response = client.get("/fruits/cheapest")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "banana"
    assert body["price"] == 0.75


# ---------- Positive: in_season filter ----------

def test_list_fruits_in_season_true_filters_correctly():
    """GET /fruits?in_season=true returns only in-season fruits."""
    seed_fruits()
    response = client.get("/fruits?in_season=true")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert all(f["in_season"] is True for f in body)
    assert {f["name"] for f in body} == {"apple", "banana"}


def test_list_fruits_in_season_false_filters_correctly():
    """GET /fruits?in_season=false returns only out-of-season fruits."""
    seed_fruits()
    response = client.get("/fruits?in_season=false")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "cherry"
    assert body[0]["in_season"] is False


# ---------- Negative: 404 on unknown id ----------

def test_get_unknown_fruit_returns_404():
    """GET /fruits/999 with no such fruit returns 404."""
    response = client.get("/fruits/999")
    assert response.status_code == 404


def test_put_unknown_fruit_returns_404():
    """PUT /fruits/999 for a non-existent fruit returns 404."""
    payload = {"name": "ghost", "price": 1.0, "in_season": False}
    response = client.put("/fruits/999", json=payload)
    assert response.status_code == 404


def test_delete_unknown_fruit_returns_404():
    """DELETE /fruits/999 for a non-existent fruit returns 404."""
    response = client.delete("/fruits/999")
    assert response.status_code == 404


# ---------- Negative: 422 on invalid body ----------

def test_post_missing_name_returns_422():
    """POST /fruits without the required 'name' field returns 422."""
    payload = {"price": 1.5, "in_season": True}  # no 'name'
    response = client.post("/fruits", json=payload)
    assert response.status_code == 422


def test_post_wrong_type_for_price_returns_422():
    """POST /fruits with a non-numeric price returns 422."""
    payload = {"name": "apple", "price": "not a number", "in_season": True}
    response = client.post("/fruits", json=payload)
    assert response.status_code == 422


# ---------- Negative: cheapest on empty store ----------

def test_cheapest_on_empty_store_returns_404():
    """GET /fruits/cheapest when no fruits exist returns 404."""
    response = client.get("/fruits/cheapest")
    assert response.status_code == 404