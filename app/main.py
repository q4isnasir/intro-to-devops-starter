from fastapi import FastAPI
from app.handlers import router

app = FastAPI(title="FruitAPI")
app.include_router(router)
