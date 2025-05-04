import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
import database.connection as db_connection
from database.migrations.migration_001_create_reviews_table import CreateReviewsTable
from database.migrations.migration_002_create_ml_outputs_table import CreateMLOutputsTable

async def run_migrations():
    await db_connection.connect_to_db()
    async with db_connection.db_pool.acquire() as connection:
        print("🔹 Running migrations...")
        await CreateReviewsTable().up(connection)
        print("✅ Created reviews table.")
        await CreateMLOutputsTable().up(connection)
        print("✅ Created ml_outputs table.")
    await db_connection.close_db_connection()

if __name__ == "__main__":
    asyncio.run(run_migrations())
