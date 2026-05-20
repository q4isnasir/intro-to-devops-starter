"""Integration tests for FruitAPI.

These tests assume the app is already running and reachable at BASE_URL.
Start the server in another terminal first:

    uvicorn app.main:app --reload

Then run:

    BASE_URL=http://localhost:8000 pytest tests/ -v
"""
import os
import pytest
import requests

# Where the running app lives. Falls back to localhost:8000 if not set.
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")


@pytest.fixture(autouse=True)
def clean_store_between_tests():
    """Wipes any fruits left over from previous tests by deleting them.

    Integration tests can't reach inside the app's memory like unit tests can,
    so we clean up via the API itself: list everything, delete each one.
    """
    response = requests.get(f"{BASE_URL}/fruits")
    if response.status_code == 200:
        for fruit in response.json():
            requests.delete(f"{BASE_URL}/fruits/{fruit['id']}")
    yield


# ---------- Health check ----------

def test_health_endpoint_returns_ok():
    """GET /health returns 200 and {"status": "ok"}."""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------- Full CRUD lifecycle ----------

def test_full_crud_lifecycle():
    """POST → GET → PUT → DELETE → GET (404). One fruit, all the way through."""
    # CREATE
    create_payload = {"name": "kiwi", "price": 2.0, "in_season": True}
    create_resp = requests.post(f"{BASE_URL}/fruits", json=create_payload)
    assert create_resp.status_code == 201
    fruit_id = create_resp.json()["id"]

    # READ
    get_resp = requests.get(f"{BASE_URL}/fruits/{fruit_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "kiwi"

    # UPDATE
    update_payload = {"name": "kiwi", "price": 2.5, "in_season": False}
    put_resp = requests.put(f"{BASE_URL}/fruits/{fruit_id}", json=update_payload)
    assert put_resp.status_code == 200
    assert put_resp.json()["price"] == 2.5
    assert put_resp.json()["in_season"] is False

    # DELETE
    delete_resp = requests.delete(f"{BASE_URL}/fruits/{fruit_id}")
    assert delete_resp.status_code == 204

    # READ AGAIN → 404
    final_get = requests.get(f"{BASE_URL}/fruits/{fruit_id}")
    assert final_get.status_code == 404


# ---------- Cheapest consistency ----------

def test_cheapest_matches_minimum_price_in_list():
    """Price from /fruits/cheapest matches min(price) from /fruits list."""
    fruits_to_add = [
        {"name": "apple", "price": 1.50, "in_season": True},
        {"name": "banana", "price": 0.75, "in_season": True},
        {"name": "cherry", "price": 3.00, "in_season": False},
    ]
    for f in fruits_to_add:
        requests.post(f"{BASE_URL}/fruits", json=f)

    list_resp = requests.get(f"{BASE_URL}/fruits")
    assert list_resp.status_code == 200
    min_price_from_list = min(f["price"] for f in list_resp.json())

    cheapest_resp = requests.get(f"{BASE_URL}/fruits/cheapest")
    assert cheapest_resp.status_code == 200
    assert cheapest_resp.json()["price"] == min_price_from_list


# ---------- Extra scenario: created fruit appears in list ----------

def test_created_fruit_appears_in_list():
    """After POST /fruits, the new fruit shows up in GET /fruits."""
    payload = {"name": "pear", "price": 1.25, "in_season": True}
    create_resp = requests.post(f"{BASE_URL}/fruits", json=payload)
    assert create_resp.status_code == 201
    created_id = create_resp.json()["id"]

    list_resp = requests.get(f"{BASE_URL}/fruits")
    assert list_resp.status_code == 200
    ids_in_list = [f["id"] for f in list_resp.json()]
    assert created_id in ids_in_list
