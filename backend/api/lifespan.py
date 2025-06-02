from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.database.connection import connect_to_db, close_db_connection, test_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    await connect_to_db()
    await test_connection()

    yield

    # On shutdown
    await close_db_connection()
