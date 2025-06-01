from backend.database.migrations.base_migration import BaseMigration

class CreateReviewsTable(BaseMigration):
    async def up(self, connection):
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id BIGSERIAL PRIMARY KEY,
                
                -- Platform-specific identifiers
                external_review_id TEXT NOT NULL,
                app_id TEXT NOT NULL,
                platform TEXT NOT NULL CHECK (platform IN ('google', 'apple')),
                
                -- Review metadata
                review_date TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                -- User information
                user_name TEXT,
                user_image TEXT,
                
                -- Review content
                title TEXT,
                content TEXT NOT NULL,
                rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
                
                -- App version information
                app_version TEXT,
                review_created_version TEXT,
                
                -- Engagement metrics
                likes_count INTEGER DEFAULT 0,
                thumbs_up_count INTEGER DEFAULT 0,
                
                -- Reply information
                reply_content TEXT,
                replied_at TIMESTAMP WITH TIME ZONE,
                
                -- Additional metadata
                language TEXT DEFAULT 'en',
                raw_data JSONB,
                
                -- Constraints
                UNIQUE(external_review_id, platform, app_id)
            );
        """)
        
        # Create indexes
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_app_platform ON reviews(app_id, platform);
        """)
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_external_id ON reviews(external_review_id);
        """)
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(review_date);
        """)
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);
        """)
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_updated_at ON reviews(updated_at);
        """)
        
        # Platform-specific indexes
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_google_thumbs ON reviews(thumbs_up_count) 
            WHERE platform = 'google';
        """)
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_apple_title ON reviews(title) 
            WHERE platform = 'apple' AND title IS NOT NULL;
        """)

    async def down(self, connection):
        await connection.execute("DROP TABLE IF EXISTS reviews CASCADE;")
        
# from backend.database.migrations.base_migration import BaseMigration

# class CreateReviewsTable(BaseMigration):
#     async def up(self, connection):
#         await connection.execute("""
#             CREATE TABLE IF NOT EXISTS reviews (
#                 id BIGSERIAL PRIMARY KEY,
#                 app_id TEXT NOT NULL,
#                 platform TEXT NOT NULL CHECK (platform IN ('google', 'apple')),
#                 date TIMESTAMP WITH TIME ZONE NOT NULL,
#                 user_name TEXT,
#                 user_image TEXT,
#                 content TEXT NOT NULL,
#                 rating SMALLINT CHECK (rating BETWEEN 1 AND 5),
#                 app_version TEXT,
#                 replies JSONB,
#                 likes_count INTEGER DEFAULT 0,
#                 language TEXT DEFAULT 'en',
#                 created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
#                 updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
#             );
#         """)
#         await connection.execute("""
#             CREATE INDEX IF NOT EXISTS idx_reviews_app_id ON reviews(app_id);
#         """)
#         await connection.execute("""
#             CREATE INDEX IF NOT EXISTS idx_reviews_platform ON reviews(platform);
#         """)
#         await connection.execute("""
#             CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(date);
#         """)

#     async def down(self, connection):
#         await connection.execute("DROP TABLE IF EXISTS reviews CASCADE;")
