import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
from backend.database import connection as db_connection
from backend.database.migrations.migration_001_create_reviews_table import CreateReviewsTable
from backend.database.migrations.migration_002_create_ml_outputs_table import CreateMLOutputsTable

async def run_migrations():
    try:
        print("🔹 Connecting to database...")
        await db_connection.connect_to_db()
        
        async with db_connection.db_pool.acquire() as connection:
            print("🔹 Running migrations...")
            
            # Migration 001
            await CreateReviewsTable().up(connection)
            print("✅ Migration 001: Created reviews table.")
            
            # Migration 002
            await CreateMLOutputsTable().up(connection)
            print("✅ Migration 002: Created ml_outputs table.")
            
        print("🎉 All migrations completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print(f"Error details: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e
        
    finally:
        await db_connection.close_db_connection()
        print("🔹 Database connection closed.")

async def rollback_migrations():
    """Rollback all migrations - use with caution!"""
    try:
        print("🔹 Connecting to database...")
        await db_connection.connect_to_db()
        
        async with db_connection.db_pool.acquire() as connection:
            print("🔹 Rolling back migrations...")
            
            # Rollback in reverse order
            await CreateMLOutputsTable().down(connection)
            print("✅ Rolled back: ml_outputs table.")
            
            await CreateReviewsTable().down(connection)
            print("✅ Rolled back: reviews table.")
            
        print("🎉 All migrations rolled back successfully!")
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        raise e
        
    finally:
        await db_connection.close_db_connection()
        print("🔹 Database connection closed.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Migration Tool')
    parser.add_argument('--rollback', action='store_true', help='Rollback migrations')
    args = parser.parse_args()
    
    if args.rollback:
        print("⚠️  WARNING: This will rollback all migrations and delete data!")
        confirm = input("Are you sure? Type 'yes' to confirm: ")
        if confirm.lower() == 'yes':
            asyncio.run(rollback_migrations())
        else:
            print("Rollback cancelled.")
    else:
        asyncio.run(run_migrations())

# import os
# from dotenv import load_dotenv
# load_dotenv()

# import asyncio
# import database.connection as db_connection
# from database.migrations.migration_001_create_reviews_table import CreateReviewsTable
# from database.migrations.migration_002_create_ml_outputs_table import CreateMLOutputsTable

# async def run_migrations():
#     await db_connection.connect_to_db()
#     async with db_connection.db_pool.acquire() as connection:
#         print("🔹 Running migrations...")
#         await CreateReviewsTable().up(connection)
#         print("✅ Created reviews table.")
#         await CreateMLOutputsTable().up(connection)
#         print("✅ Created ml_outputs table.")
#     await db_connection.close_db_connection()

# if __name__ == "__main__":
#     asyncio.run(run_migrations())
