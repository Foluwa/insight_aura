from backend.database.migrations.base_migration import BaseMigration

class CreateReviewsTable(BaseMigration):
    async def up(self, connection):
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id BIGSERIAL PRIMARY KEY,
                app_id TEXT NOT NULL,
                platform TEXT NOT NULL CHECK (platform IN ('google', 'apple')),
                date TIMESTAMP WITH TIME ZONE NOT NULL,
                user_name TEXT,
                user_image TEXT,
                content TEXT NOT NULL,
                rating SMALLINT CHECK (rating BETWEEN 1 AND 5),
                app_version TEXT,
                replies JSONB,
                likes_count INTEGER DEFAULT 0,
                language TEXT DEFAULT 'en',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_app_id ON reviews(app_id);
        """)
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_platform ON reviews(platform);
        """)
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(date);
        """)

    async def down(self, connection):
        await connection.execute("DROP TABLE IF EXISTS reviews CASCADE;")
