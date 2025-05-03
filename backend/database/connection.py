import asyncpg
import os
from typing import Optional, AsyncGenerator

# Read DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

db_pool: Optional[asyncpg.pool.Pool] = None

async def connect_to_db():
    global db_pool
    if not DATABASE_URL:
        raise Exception("DATABASE_URL environment variable not set.")

    db_pool = await asyncpg.create_pool(
        dsn=DATABASE_URL,
        min_size=1,
        max_size=5,
        command_timeout=60,
    )
    print("✅ Successfully connected to PostgreSQL!")

async def close_db_connection():
    global db_pool
    if db_pool:
        await db_pool.close()
        print("✅ PostgreSQL connection closed.")

async def test_connection():
    global db_pool
    if not db_pool:
        raise Exception("Database not connected.")

    async with db_pool.acquire() as connection:
        result = await connection.fetchval('SELECT 1')
        if result == 1:
            print("✅ Database connection test passed!")
        else:
            raise Exception("❌ Database connection test failed.")


async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    global db_pool
    if not db_pool:
        raise Exception("Database not connected.")

    async with db_pool.acquire() as connection:
        yield connection
