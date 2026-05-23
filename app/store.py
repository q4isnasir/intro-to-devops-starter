"""
MySQL-based fruit storage using SQLAlchemy.

The database connection details come from environment variables, so this
same file can run locally with the Docker MySQL container, and later in AWS
with RDS.

This file also includes FakeFruitStore, which is an in-memory version used
for fast and isolated unit tests. The route handlers use `get_store()`, which
normally gives them the real database store, but tests can replace it through
FastAPI's dependency_overrides.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.models import Fruit, FruitCreate


# Database connection setup


# Load the database settings from environment variables.
# If nothing is provided, these defaults point to the local Docker MySQL
# container used during development.
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "fruituser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "fruitpass")
DB_NAME = os.getenv("DB_NAME", "fruitdb")

# SQLAlchemy connection string in the format:
# mysql+pymysql://user:password@host:port/database
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Create the SQLAlchemy engine, which manages database connections for us.
# pool_pre_ping=True helps avoid using stale or disconnected MySQL connections.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# SessionLocal is used to create database sessions when we need to run queries.
# Each session represents one unit of work with the database.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base class used by SQLAlchemy for defining database table models.
Base = declarative_base()


# Table definition (the ORM model)


class FruitRow(Base):
    """
    Represents a single record in the `fruits` database table.

    This is the database version of a fruit. The API response model is the
    `Fruit` model from app/models.py. Keeping them separate makes it easier to
    change the storage layer without changing the API structure.
    """

    __tablename__ = "fruits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    in_season = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


def create_tables() -> None:
    """
    Create the `fruits` table if it has not been created yet.

    This can be called more than once safely. If the table already exists,
    SQLAlchemy simply leaves it as it is. The app calls this during startup.
    """
    Base.metadata.create_all(bind=engine)


# Real (MySQL-backed) store


class FruitStore:
    """Fruit store that uses MySQL. This is used by the app and integration tests."""

    def get_all(self, in_season: Optional[bool] = None) -> List[Fruit]:
        """Get all fruits, with an optional filter for seasonal fruits."""
        with SessionLocal() as session:
            query = session.query(FruitRow)
            if in_season is not None:
                query = query.filter(FruitRow.in_season == in_season)
            rows = query.all()
            return [self._row_to_fruit(row) for row in rows]

    def get(self, fruit_id: int) -> Optional[Fruit]:
        """Get a single fruit by its id. Return None if it does not exist."""
        with SessionLocal() as session:
            row = session.get(FruitRow, fruit_id)
            return self._row_to_fruit(row) if row else None

    def add(self, fruit: FruitCreate) -> Fruit:
        """Add a new fruit to the database and return the saved version."""
        with SessionLocal() as session:
            row = FruitRow(
                name=fruit.name,
                price=fruit.price,
                in_season=fruit.in_season,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return self._row_to_fruit(row)

    def update(self, fruit_id: int, fruit: FruitCreate) -> Optional[Fruit]:
        """Update an existing fruit. Return None if the fruit is not found."""
        with SessionLocal() as session:
            row = session.get(FruitRow, fruit_id)
            if row is None:
                return None
            row.name = fruit.name
            row.price = fruit.price
            row.in_season = fruit.in_season
            session.commit()
            session.refresh(row)
            return self._row_to_fruit(row)

    def delete(self, fruit_id: int) -> bool:
        """Remove a fruit by id. Return True if it was deleted, otherwise False."""
        with SessionLocal() as session:
            row = session.get(FruitRow, fruit_id)
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True

    def cheapest(self) -> Optional[Fruit]:
        """Find the cheapest fruit. Return None if there are no fruits."""
        with SessionLocal() as session:
            row = session.query(FruitRow).order_by(FruitRow.price.asc()).first()
            return self._row_to_fruit(row) if row else None

    def clear(self) -> None:
        """Remove all fruits from the table. Mainly used to reset integration tests."""
        with SessionLocal() as session:
            session.query(FruitRow).delete()
            session.commit()

    @staticmethod
    def _row_to_fruit(row: FruitRow) -> Fruit:
        """Turn a database row into the Fruit model used by the API."""
        return Fruit(
            id=row.id,
            name=row.name,
            price=row.price,
            in_season=row.in_season,
            created_at=row.created_at,
        )


# Fake (in-memory) store — used ONLY by unit tests


class FakeFruitStore:
    """
    Simple in-memory version of the fruit store.

    It follows the same interface as FruitStore, but stores everything in a
    dictionary instead of MySQL. This keeps unit tests quick and avoids needing
    a real database for them.
    """

    def __init__(self) -> None:
        self._fruits: Dict[int, Fruit] = {}
        self._next_id: int = 1

    def get_all(self, in_season: Optional[bool] = None) -> List[Fruit]:
        fruits = list(self._fruits.values())
        if in_season is not None:
            fruits = [f for f in fruits if f.in_season == in_season]
        return fruits

    def get(self, fruit_id: int) -> Optional[Fruit]:
        return self._fruits.get(fruit_id)

    def add(self, fruit: FruitCreate) -> Fruit:
        new = Fruit(
            id=self._next_id,
            name=fruit.name,
            price=fruit.price,
            in_season=fruit.in_season,
            created_at=datetime.utcnow(),
        )
        self._fruits[self._next_id] = new
        self._next_id += 1
        return new

    def update(self, fruit_id: int, fruit: FruitCreate) -> Optional[Fruit]:
        existing = self._fruits.get(fruit_id)
        if existing is None:
            return None
        updated = Fruit(
            id=existing.id,
            name=fruit.name,
            price=fruit.price,
            in_season=fruit.in_season,
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

    def clear(self) -> None:
        self._fruits.clear()
        self._next_id = 1


# Dependency provider — handlers get their store through this


# One shared real store instance used by the application.
_real_store = FruitStore()


def get_store() -> FruitStore:
    """
    Return the store that the route handlers should use.

    In normal app usage, this returns the real MySQL-backed store. In tests,
    it can be overridden with `app.dependency_overrides[get_store] = ...`
    to use FakeFruitStore instead.
    """
    return _real_store