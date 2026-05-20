from datetime import datetime, timezone
from typing import Optional
from app.models import Fruit, FruitCreate


class FruitStore:
    def __init__(self):
        self._fruits: dict[int, Fruit] = {}
        self._next_id: int = 1

    def add(self, data: FruitCreate) -> Fruit:
        fruit = Fruit(
            id=self._next_id,
            name=data.name,
            price=data.price,
            in_season=data.in_season,
            created_at=datetime.now(timezone.utc),
        )
        self._fruits[self._next_id] = fruit
        self._next_id += 1
        return fruit

    def get_all(self, in_season: Optional[bool] = None) -> list[Fruit]:
        fruits = list(self._fruits.values())
        if in_season is not None:
            fruits = [f for f in fruits if f.in_season == in_season]
        return fruits

    def get(self, fruit_id: int) -> Optional[Fruit]:
        return self._fruits.get(fruit_id)

    def update(self, fruit_id: int, data: FruitCreate) -> Optional[Fruit]:
        if fruit_id not in self._fruits:
            return None
        existing = self._fruits[fruit_id]
        updated = Fruit(
            id=existing.id,
            name=data.name,
            price=data.price,
            in_season=data.in_season,
            created_at=existing.created_at,
        )
        self._fruits[fruit_id] = updated
        return updated

    def delete(self, fruit_id: int) -> bool:
        if fruit_id not in self._fruits:
            return False
        del self._fruits[fruit_id]
        return True

    def cheapest(self) -> Optional[Fruit]:
        if not self._fruits:
            return None
        return min(self._fruits.values(), key=lambda f: f.price)
