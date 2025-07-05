from backend.database.migrations.base_migration import BaseMigration

class CreateAppsTable(BaseMigration):
    async def up(self, connection):
        # Apps configuration table
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS apps (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                apple_app_id TEXT,
                google_package_name TEXT,
                internal_app_id TEXT UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT true,
                
                -- Scraping configuration
                scraping_enabled BOOLEAN DEFAULT true,
                reviews_per_run INTEGER DEFAULT 100,
                scraping_frequency_hours INTEGER DEFAULT 6,
                
                -- Rate limiting per app
                rate_limit_delay REAL DEFAULT 1.0,
                max_retries INTEGER DEFAULT 3,
                
                -- Metadata
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_scraped_at TIMESTAMP WITH TIME ZONE,
                
                -- Constraints
                CHECK (apple_app_id IS NOT NULL OR google_package_name IS NOT NULL)
            );
        """)
        
        # Scraping jobs tracking table
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS scraping_jobs (
                id BIGSERIAL PRIMARY KEY,
                app_id BIGINT NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
                platform TEXT NOT NULL CHECK (platform IN ('apple', 'google', 'both')),
                
                -- Job status
                status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
                
                -- Execution details
                started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                completed_at TIMESTAMP WITH TIME ZONE,
                dag_run_id TEXT,
                task_instance_id TEXT,
                
                -- Results
                reviews_requested INTEGER,
                reviews_scraped INTEGER DEFAULT 0,
                reviews_inserted INTEGER DEFAULT 0,
                reviews_failed INTEGER DEFAULT 0,
                
                -- Error handling
                error_message TEXT,
                error_traceback TEXT,
                retry_count INTEGER DEFAULT 0,
                
                -- Performance metrics
                scraping_duration_seconds REAL,
                insertion_duration_seconds REAL,
                
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Scraping metrics table for monitoring
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS scraping_metrics (
                id BIGSERIAL PRIMARY KEY,
                app_id BIGINT NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
                platform TEXT NOT NULL,
                
                -- Time-based metrics
                date DATE NOT NULL,
                hour INTEGER CHECK (hour >= 0 AND hour <= 23),
                
                -- Scraping metrics
                total_requests INTEGER DEFAULT 0,
                successful_requests INTEGER DEFAULT 0,
                failed_requests INTEGER DEFAULT 0,
                
                -- Review metrics
                reviews_scraped INTEGER DEFAULT 0,
                reviews_inserted INTEGER DEFAULT 0,
                average_rating REAL,
                
                -- Performance metrics
                average_response_time_ms REAL,
                total_duration_seconds REAL,
                
                -- Rate limiting metrics
                rate_limit_hits INTEGER DEFAULT 0,
                proxy_rotations INTEGER DEFAULT 0,
                
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                -- Unique constraint for aggregation
                UNIQUE(app_id, platform, date, hour)
            );
        """)
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_apps_internal_app_id ON apps(internal_app_id);",
            "CREATE INDEX IF NOT EXISTS idx_apps_active ON apps(is_active) WHERE is_active = true;",
            "CREATE INDEX IF NOT EXISTS idx_apps_scraping_enabled ON apps(scraping_enabled) WHERE scraping_enabled = true;",
            
            "CREATE INDEX IF NOT EXISTS idx_scraping_jobs_app_id ON scraping_jobs(app_id);",
            "CREATE INDEX IF NOT EXISTS idx_scraping_jobs_status ON scraping_jobs(status);",
            "CREATE INDEX IF NOT EXISTS idx_scraping_jobs_started_at ON scraping_jobs(started_at);",
            "CREATE INDEX IF NOT EXISTS idx_scraping_jobs_dag_run_id ON scraping_jobs(dag_run_id);",
            
            "CREATE INDEX IF NOT EXISTS idx_scraping_metrics_app_platform ON scraping_metrics(app_id, platform);",
            "CREATE INDEX IF NOT EXISTS idx_scraping_metrics_date ON scraping_metrics(date);",
            
            "CREATE INDEX IF NOT EXISTS idx_reviews_app_platform_date ON reviews(app_id, platform, review_date);",
        ]
        
        for index_sql in indexes:
            await connection.execute(index_sql)
        
        # Insert sample apps
        await connection.execute("""
            INSERT INTO apps (name, apple_app_id, google_package_name, internal_app_id, reviews_per_run) 
            VALUES 
                ('Slack', '618783545', 'com.Slack', 'slack', 200),
                ('Minecraft', '479516143', 'com.mojang.minecraftpe', 'minecraft', 150),
                ('WhatsApp', '310633997', 'com.whatsapp', 'whatsapp', 300),
                ('Instagram', '389801252', 'com.instagram.android', 'instagram', 250)
            ON CONFLICT (internal_app_id) DO NOTHING;
        """)

    async def down(self, connection):
        await connection.execute("DROP TABLE IF EXISTS scraping_metrics CASCADE;")
        await connection.execute("DROP TABLE IF EXISTS scraping_jobs CASCADE;")
        await connection.execute("DROP TABLE IF EXISTS apps CASCADE;")