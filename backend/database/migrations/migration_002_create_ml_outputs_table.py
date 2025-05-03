from backend.database.migrations.base_migration import BaseMigration

class CreateMLOutputsTable(BaseMigration):
    async def up(self, connection):
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS ml_outputs (
                id BIGSERIAL PRIMARY KEY,
                review_id BIGINT NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
                model_name TEXT NOT NULL,
                model_task TEXT NOT NULL,
                sentiment TEXT CHECK (sentiment IN ('positive', 'neutral', 'negative')),
                sentiment_score REAL,
                sentiment_analysis JSONB,
                summary TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_ml_outputs_review_id ON ml_outputs(review_id);
        """)
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_ml_outputs_model_name ON ml_outputs(model_name);
        """)
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_ml_outputs_model_task ON ml_outputs(model_task);
        """)

    async def down(self, connection):
        await connection.execute("DROP TABLE IF EXISTS ml_outputs CASCADE;")
