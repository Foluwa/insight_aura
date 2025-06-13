# #!/usr/bin/env python3
# # File: safe_migrate.py (create this in your project root)

# import asyncio
# import asyncpg
# import os
# from dotenv import load_dotenv

# load_dotenv()
# DATABASE_URL = os.getenv("DATABASE_URL")

# async def check_table_exists(connection, table_name):
#     """Check if a table exists"""
#     result = await connection.fetchval("""
#         SELECT EXISTS (
#             SELECT FROM information_schema.tables 
#             WHERE table_schema = 'public' AND table_name = $1
#         )
#     """, table_name)
#     return result

# async def check_column_exists(connection, table_name, column_name):
#     """Check if a column exists in a table"""
#     result = await connection.fetchval("""
#         SELECT EXISTS (
#             SELECT FROM information_schema.columns 
#             WHERE table_name = $1 AND column_name = $2
#         )
#     """, table_name, column_name)
#     return result

# async def safe_migrate():
#     """Safely migrate database, handling existing tables"""
#     if not DATABASE_URL:
#         print("❌ DATABASE_URL not set!")
#         return
    
#     try:
#         print("🔹 Connecting to database...")
#         connection = await asyncpg.connect(DATABASE_URL)
        
#         # Check if reviews table exists
#         reviews_exists = await check_table_exists(connection, 'reviews')
        
#         if reviews_exists:
#             print("⚠️  Reviews table already exists. Checking structure...")
            
#             # Check if it has the new structure
#             has_external_review_id = await check_column_exists(connection, 'reviews', 'external_review_id')
            
#             if not has_external_review_id:
#                 print("🔄 Old schema detected. Options:")
#                 print("1. Drop and recreate table (WILL LOSE DATA)")
#                 print("2. Alter existing table (preserve data)")
#                 print("3. Cancel")
                
#                 choice = input("Choose option (1/2/3): ").strip()
                
#                 if choice == "1":
#                     print("🗑️  Dropping existing reviews table...")
#                     await connection.execute("DROP TABLE IF EXISTS reviews CASCADE;")
#                     await create_new_reviews_table(connection)
#                 elif choice == "2":
#                     print("🔧 Altering existing table...")
#                     await alter_reviews_table(connection)
#                 else:
#                     print("❌ Migration cancelled.")
#                     return
#             else:
#                 print("✅ Reviews table already has new structure")
#         else:
#             print("🆕 Creating new reviews table...")
#             await create_new_reviews_table(connection)
        
#         # Handle ml_outputs table
#         ml_outputs_exists = await check_table_exists(connection, 'ml_outputs')
        
#         if not ml_outputs_exists:
#             print("🆕 Creating ml_outputs table...")
#             await create_ml_outputs_table(connection)
#         else:
#             print("✅ ml_outputs table already exists")
        
#         print("🎉 Migration completed successfully!")
        
#     except Exception as e:
#         print(f"❌ Migration failed: {e}")
#         import traceback
#         traceback.print_exc()
        
#     finally:
#         if 'connection' in locals():
#             await connection.close()

# async def create_new_reviews_table(connection):
#     """Create the new reviews table"""
#     await connection.execute("""
#         CREATE TABLE reviews (
#             id BIGSERIAL PRIMARY KEY,
            
#             -- Platform-specific identifiers
#             external_review_id TEXT NOT NULL,
#             app_id TEXT NOT NULL,
#             platform TEXT NOT NULL CHECK (platform IN ('google', 'apple')),
            
#             -- Review metadata
#             review_date TIMESTAMP WITH TIME ZONE NOT NULL,
#             created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
#             updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
#             -- User information
#             user_name TEXT,
#             user_image TEXT,
            
#             -- Review content
#             title TEXT,
#             content TEXT NOT NULL,
#             rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
            
#             -- App version information
#             app_version TEXT,
#             review_created_version TEXT,
            
#             -- Engagement metrics
#             likes_count INTEGER DEFAULT 0,
#             thumbs_up_count INTEGER DEFAULT 0,
            
#             -- Reply information
#             reply_content TEXT,
#             replied_at TIMESTAMP WITH TIME ZONE,
            
#             -- Additional metadata
#             language TEXT DEFAULT 'en',
#             raw_data JSONB,
            
#             -- Constraints
#             UNIQUE(external_review_id, platform, app_id)
#         );
#     """)
    
#     # Create indexes
#     await create_reviews_indexes(connection)
#     print("✅ Reviews table created with new schema")

# async def alter_reviews_table(connection):
#     """Alter existing reviews table to match new schema"""
    
#     # First, let's see what columns we need to add
#     new_columns = [
#         ("external_review_id", "TEXT"),
#         ("review_date", "TIMESTAMP WITH TIME ZONE"),
#         ("user_image", "TEXT"),
#         ("title", "TEXT"),
#         ("review_created_version", "TEXT"),
#         ("thumbs_up_count", "INTEGER DEFAULT 0"),
#         ("reply_content", "TEXT"),
#         ("replied_at", "TIMESTAMP WITH TIME ZONE"),
#         ("raw_data", "JSONB"),
#     ]
    
#     for column_name, column_type in new_columns:
#         column_exists = await check_column_exists(connection, 'reviews', column_name)
#         if not column_exists:
#             print(f"  Adding column: {column_name}")
#             await connection.execute(f"ALTER TABLE reviews ADD COLUMN {column_name} {column_type};")
    
#     # Rename 'date' to 'review_date' if needed
#     date_exists = await check_column_exists(connection, 'reviews', 'date')
#     review_date_exists = await check_column_exists(connection, 'reviews', 'review_date')
    
#     if date_exists and not review_date_exists:
#         print("  Renaming 'date' column to 'review_date'")
#         await connection.execute("ALTER TABLE reviews RENAME COLUMN date TO review_date;")
    
#     # Update external_review_id from existing id if it's empty
#     print("  Populating external_review_id...")
#     await connection.execute("""
#         UPDATE reviews 
#         SET external_review_id = COALESCE(external_review_id, id::text)
#         WHERE external_review_id IS NULL;
#     """)
    
#     # Make external_review_id NOT NULL
#     await connection.execute("ALTER TABLE reviews ALTER COLUMN external_review_id SET NOT NULL;")
    
#     # Add unique constraint if it doesn't exist
#     try:
#         await connection.execute("""
#             ALTER TABLE reviews 
#             ADD CONSTRAINT reviews_external_review_id_platform_app_id_key 
#             UNIQUE (external_review_id, platform, app_id);
#         """)
#         print("  Added unique constraint")
#     except:
#         print("  Unique constraint already exists or couldn't be added")
    
#     # Create indexes
#     await create_reviews_indexes(connection)
#     print("✅ Reviews table altered to match new schema")

# async def create_reviews_indexes(connection):
#     """Create indexes for reviews table"""
#     indexes = [
#         "CREATE INDEX IF NOT EXISTS idx_reviews_app_platform ON reviews(app_id, platform);",
#         "CREATE INDEX IF NOT EXISTS idx_reviews_external_id ON reviews(external_review_id);",
#         "CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(review_date);",
#         "CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);",
#         "CREATE INDEX IF NOT EXISTS idx_reviews_updated_at ON reviews(updated_at);",
#         """CREATE INDEX IF NOT EXISTS idx_reviews_google_thumbs ON reviews(thumbs_up_count) 
#            WHERE platform = 'google';""",
#         """CREATE INDEX IF NOT EXISTS idx_reviews_apple_title ON reviews(title) 
#            WHERE platform = 'apple' AND title IS NOT NULL;"""
#     ]
    
#     for index_sql in indexes:
#         try:
#             await connection.execute(index_sql)
#         except Exception as e:
#             print(f"  Warning: Could not create index: {e}")

# async def create_ml_outputs_table(connection):
#     """Create ML outputs table"""
#     await connection.execute("""
#         CREATE TABLE ml_outputs (
#             id BIGSERIAL PRIMARY KEY,
#             review_id BIGINT NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
#             model_name TEXT NOT NULL,
#             model_task TEXT NOT NULL,
#             sentiment TEXT CHECK (sentiment IN ('positive', 'neutral', 'negative')),
#             sentiment_score REAL,
#             sentiment_analysis JSONB,
#             summary TEXT,
#             created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
#         );
#     """)
    
#     # Create indexes
#     indexes = [
#         "CREATE INDEX IF NOT EXISTS idx_ml_outputs_review_id ON ml_outputs(review_id);",
#         "CREATE INDEX IF NOT EXISTS idx_ml_outputs_model_name ON ml_outputs(model_name);",
#         "CREATE INDEX IF NOT EXISTS idx_ml_outputs_model_task ON ml_outputs(model_task);"
#     ]
    
#     for index_sql in indexes:
#         await connection.execute(index_sql)
    
#     print("✅ ml_outputs table created")

# if __name__ == "__main__":
#     asyncio.run(safe_migrate())