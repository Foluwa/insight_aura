# #!/usr/bin/env python3
# # File: inspect_db.py (create this in your project root)

# import asyncio
# import asyncpg
# import os
# from dotenv import load_dotenv

# load_dotenv()
# DATABASE_URL = os.getenv("DATABASE_URL")

# async def inspect_database():
#     """Inspect current database structure"""
#     if not DATABASE_URL:
#         print("❌ DATABASE_URL not set!")
#         return
    
#     try:
#         print("🔹 Connecting to database...")
#         connection = await asyncpg.connect(DATABASE_URL)
        
#         # Check existing tables
#         print("\n📋 Existing tables:")
#         tables = await connection.fetch("""
#             SELECT table_name FROM information_schema.tables 
#             WHERE table_schema = 'public'
#         """)
        
#         for table in tables:
#             print(f"  - {table['table_name']}")
        
#         # Check reviews table structure if it exists
#         reviews_exists = any(table['table_name'] == 'reviews' for table in tables)
        
#         if reviews_exists:
#             print("\n🔍 Current reviews table structure:")
#             columns = await connection.fetch("""
#                 SELECT column_name, data_type, is_nullable, column_default
#                 FROM information_schema.columns 
#                 WHERE table_name = 'reviews'
#                 ORDER BY ordinal_position
#             """)
            
#             for col in columns:
#                 nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
#                 default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
#                 print(f"  - {col['column_name']}: {col['data_type']} {nullable}{default}")
            
#             # Check indexes
#             print("\n📊 Current indexes on reviews table:")
#             indexes = await connection.fetch("""
#                 SELECT indexname, indexdef 
#                 FROM pg_indexes 
#                 WHERE tablename = 'reviews'
#             """)
            
#             for idx in indexes:
#                 print(f"  - {idx['indexname']}")
        
#         # Check ml_outputs table if exists
#         ml_outputs_exists = any(table['table_name'] == 'ml_outputs' for table in tables)
#         if ml_outputs_exists:
#             print("\n🔍 ml_outputs table exists")
        
#         print(f"\n✅ Database inspection complete!")
        
#     except Exception as e:
#         print(f"❌ Inspection failed: {e}")
        
#     finally:
#         if 'connection' in locals():
#             await connection.close()

# if __name__ == "__main__":
#     asyncio.run(inspect_database())