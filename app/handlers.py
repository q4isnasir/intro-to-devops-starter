from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models import Fruit, FruitCreate
from app.store import FruitStore, get_store

router = APIRouter()


@router.get("/health")
def health_check():
    """Returns 200 so load balancers know the app is alive."""
    return {"status": "ok"}


@router.get("/fruits", response_model=list[Fruit])
def list_fruits(
    in_season: Optional[bool] = Query(default=None),
    store: FruitStore = Depends(get_store),
):
    """Returns all fruits. Pass ?in_season=true or ?in_season=false to filter."""
    return store.get_all(in_season=in_season)


@router.post("/fruits", response_model=Fruit, status_code=201)
def create_fruit(
    data: FruitCreate,
    store: FruitStore = Depends(get_store),
):
    """Creates a new fruit from the JSON body and returns it with its new id."""
    return store.add(data)


@router.get("/fruits/cheapest", response_model=Fruit)
def get_cheapest(store: FruitStore = Depends(get_store)):
    """Fruit with lowest price is returned, or 404 if there are none."""
    fruit = store.cheapest()
    if fruit is None:
        raise HTTPException(status_code=404, detail="No fruits available")
    return fruit


@router.get("/fruits/{fruit_id}", response_model=Fruit)
def get_fruit(fruit_id: int, store: FruitStore = Depends(get_store)):
    """Returns one fruit by id or 404 if not found."""
    fruit = store.get(fruit_id)
    if fruit is None:
        raise HTTPException(status_code=404, detail="Fruit not found")
    return fruit


@router.put("/fruits/{fruit_id}", response_model=Fruit)
def update_fruit(
    fruit_id: int,
    data: FruitCreate,
    store: FruitStore = Depends(get_store),
):
    """Replaces all fields of a fruit. Returns 404 if id doesn't exist."""
    fruit = store.update(fruit_id, data)
    if fruit is None:
        raise HTTPException(status_code=404, detail="Fruit not found")
    return fruit


@router.delete("/fruits/{fruit_id}", status_code=204)
def delete_fruit(fruit_id: int, store: FruitStore = Depends(get_store)):
    """Deletes a fruit. Returns 204 on success, 404 if missing."""
    deleted = store.delete(fruit_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Fruit not found")