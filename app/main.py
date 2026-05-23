from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.handlers import router
from app.store import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run once when the app starts: create the fruits table if it doesn't exist."""
    create_tables()
    yield
    # nothing to clean up on shutdown


app = FastAPI(title="FruitAPI", lifespan=lifespan)
app.include_router(router)