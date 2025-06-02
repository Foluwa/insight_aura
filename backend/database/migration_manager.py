import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import asyncpg

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv()

import asyncio
from backend.database import connection as db_connection
from backend.database.migrations.migration_001_create_reviews_table import CreateReviewsTable
from backend.database.migrations.migration_002_create_ml_outputs_table import CreateMLOutputsTable

class MigrationManager:
    def __init__(self):
        self.migrations = [
            ('001', 'create_reviews_table', CreateReviewsTable),
            ('002', 'create_ml_outputs_table', CreateMLOutputsTable),
        ]
    
    async def create_migrations_table(self, connection: asyncpg.Connection):
        """Create the migrations tracking table"""
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
    
    async def get_executed_migrations(self, connection: asyncpg.Connection) -> List[str]:
        """Get list of executed migrations"""
        rows = await connection.fetch("SELECT version FROM schema_migrations ORDER BY version")
        return [row['version'] for row in rows]
    
    async def mark_migration_executed(self, connection: asyncpg.Connection, version: str, name: str):
        """Mark migration as executed"""
        await connection.execute("""
            INSERT INTO schema_migrations (version, name) VALUES ($1, $2)
            ON CONFLICT (version) DO NOTHING
        """, version, name)
    
    async def unmark_migration(self, connection: asyncpg.Connection, version: str):
        """Remove migration from executed list"""
        await connection.execute("DELETE FROM schema_migrations WHERE version = $1", version)
    
    async def run_migrations(self):
        """Run all pending migrations"""
        try:
            print("🔹 Connecting to database...")
            await db_connection.connect_to_db()
            
            async with db_connection.db_pool.acquire() as connection:
                # Create migrations table if it doesn't exist
                await self.create_migrations_table(connection)
                
                # Get executed migrations
                executed = await self.get_executed_migrations(connection)
                print(f"📋 Previously executed migrations: {executed}")
                
                # Run pending migrations
                pending_count = 0
                for version, name, migration_class in self.migrations:
                    if version not in executed:
                        print(f"🔄 Running migration {version}: {name}")
                        await migration_class().up(connection)
                        await self.mark_migration_executed(connection, version, name)
                        print(f"✅ Migration {version} completed")
                        pending_count += 1
                    else:
                        print(f"⏭️  Migration {version} already executed")
                
                if pending_count == 0:
                    print("🎯 No pending migrations")
                else:
                    print(f"🎉 Successfully executed {pending_count} migrations!")
                    
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise e
            
        finally:
            await db_connection.close_db_connection()
            print("🔹 Database connection closed.")
    
    async def rollback_last_migration(self):
        """Rollback the last executed migration"""
        try:
            print("🔹 Connecting to database...")
            await db_connection.connect_to_db()
            
            async with db_connection.db_pool.acquire() as connection:
                await self.create_migrations_table(connection)
                executed = await self.get_executed_migrations(connection)
                
                if not executed:
                    print("📭 No migrations to rollback")
                    return
                
                # Get the last migration
                last_version = executed[-1]
                migration_to_rollback = None
                
                for version, name, migration_class in self.migrations:
                    if version == last_version:
                        migration_to_rollback = (version, name, migration_class)
                        break
                
                if migration_to_rollback:
                    version, name, migration_class = migration_to_rollback
                    print(f"🔄 Rolling back migration {version}: {name}")
                    await migration_class().down(connection)
                    await self.unmark_migration(connection, version)
                    print(f"✅ Migration {version} rolled back")
                else:
                    print(f"❌ Migration {last_version} not found in migration list")
                    
        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            raise e
            
        finally:
            await db_connection.close_db_connection()
            print("🔹 Database connection closed.")
    
    async def show_migration_status(self):
        """Show current migration status"""
        try:
            await db_connection.connect_to_db()
            
            async with db_connection.db_pool.acquire() as connection:
                await self.create_migrations_table(connection)
                executed = await self.get_executed_migrations(connection)
                
                print("\n📊 Migration Status:")
                print("-" * 50)
                
                for version, name, _ in self.migrations:
                    status = "✅ EXECUTED" if version in executed else "⏳ PENDING"
                    print(f"{version} | {name:<30} | {status}")
                
                print("-" * 50)
                print(f"Total: {len(self.migrations)} migrations, {len(executed)} executed, {len(self.migrations) - len(executed)} pending")
                
        except Exception as e:
            print(f"❌ Failed to show status: {e}")
            
        finally:
            await db_connection.close_db_connection()

# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Migration Manager')
    parser.add_argument('command', choices=['migrate', 'rollback', 'status'], 
                       help='Command to execute')
    
    args = parser.parse_args()
    manager = MigrationManager()
    
    if args.command == 'migrate':
        asyncio.run(manager.run_migrations())
    elif args.command == 'rollback':
        print("⚠️  WARNING: This will rollback the last migration!")
        confirm = input("Are you sure? Type 'yes' to confirm: ")
        if confirm.lower() == 'yes':
            asyncio.run(manager.rollback_last_migration())
        else:
            print("Rollback cancelled.")
    elif args.command == 'status':
        asyncio.run(manager.show_migration_status())