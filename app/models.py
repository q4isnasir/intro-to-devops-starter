from pydantic import BaseModel
from datetime import datetime


class FruitCreate(BaseModel):

    """What the client sends - updating or creatung a fruit."""
    name: str
    price: float
    in_season: bool = False


class Fruit(FruitCreate):
    """Fruit as it is stored and returnedd by the API ruit as stored (server assigned fields included as well)."""
    id: int
    created_at: datetime
