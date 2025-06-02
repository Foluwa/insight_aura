import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncpg
from backend.database.connection import get_db_connection

logger = logging.getLogger(__name__)

class AppManagementService:
    """
    Service for managing apps and scraping configurations in enterprise environment.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def get_active_apps(self) -> List[Dict[str, Any]]:
        """
        Get all active apps that are enabled for scraping.
        
        Returns:
            List of app dictionaries with configuration
        """
        async with get_db_connection() as conn:
            rows = await conn.fetch("""
                SELECT 
                    id, name, apple_app_id, google_package_name, internal_app_id,
                    reviews_per_run, scraping_frequency_hours, rate_limit_delay,
                    max_retries, last_scraped_at
                FROM apps 
                WHERE is_active = true AND scraping_enabled = true
                ORDER BY name
            """)
            
            return [dict(row) for row in rows]
    
    async def get_apps_due_for_scraping(self, buffer_minutes: int = 30) -> List[Dict[str, Any]]:
        """
        Get apps that are due for scraping based on their frequency settings.
        
        Args:
            buffer_minutes: Buffer time to avoid exact timing issues
            
        Returns:
            List of apps due for scraping
        """
        async with get_db_connection() as conn:
            rows = await conn.fetch("""
                SELECT 
                    id, name, apple_app_id, google_package_name, internal_app_id,
                    reviews_per_run, scraping_frequency_hours, rate_limit_delay,
                    max_retries, last_scraped_at
                FROM apps 
                WHERE is_active = true 
                    AND scraping_enabled = true
                    AND (
                        last_scraped_at IS NULL 
                        OR last_scraped_at <= NOW() - INTERVAL '1 hour' * scraping_frequency_hours - INTERVAL '1 minute' * $1
                    )
                ORDER BY last_scraped_at ASC NULLS FIRST
            """, buffer_minutes)
            
            return [dict(row) for row in rows]
    
    async def create_scraping_job(self, app_id: int, platform: str, 
                                dag_run_id: str, reviews_requested: int) -> int:
        """
        Create a new scraping job record.
        
        Args:
            app_id: App ID from apps table
            platform: 'apple', 'google', or 'both'
            dag_run_id: Airflow DAG run ID
            reviews_requested: Number of reviews requested
            
        Returns:
            Job ID
        """
        async with get_db_connection() as conn:
            job_id = await conn.fetchval("""
                INSERT INTO scraping_jobs (
                    app_id, platform, status, dag_run_id, reviews_requested
                ) VALUES ($1, $2, 'pending', $3, $4)
                RETURNING id
            """, app_id, platform, dag_run_id, reviews_requested)
            
            self.logger.info(f"Created scraping job {job_id} for app {app_id}, platform {platform}")
            return job_id
    
    async def update_scraping_job(self, job_id: int, status: str, 
                                **kwargs) -> None:
        """
        Update scraping job with results and metrics.
        
        Args:
            job_id: Job ID
            status: Job status ('running', 'completed', 'failed')
            **kwargs: Additional fields to update
        """
        # Build dynamic update query
        update_fields = ['status = $2', 'updated_at = NOW()']
        params = [job_id, status]
        param_index = 3
        
        for field, value in kwargs.items():
            if field in ['reviews_scraped', 'reviews_inserted', 'reviews_failed', 
                        'error_message', 'error_traceback', 'retry_count',
                        'scraping_duration_seconds', 'insertion_duration_seconds',
                        'task_instance_id']:
                update_fields.append(f"{field} = ${param_index}")
                params.append(value)
                param_index += 1
        
        if status in ['completed', 'failed', 'cancelled']:
            update_fields.append(f"completed_at = ${param_index}")
            params.append(datetime.now())
        
        query = f"""
            UPDATE scraping_jobs 
            SET {', '.join(update_fields)}
            WHERE id = $1
        """
        
        async with get_db_connection() as conn:
            await conn.execute(query, *params)
        
        self.logger.info(f"Updated scraping job {job_id} with status {status}")
    
    async def update_app_last_scraped(self, app_id: int) -> None:
        """Update the last scraped timestamp for an app."""
        async with get_db_connection() as conn:
            await conn.execute("""
                UPDATE apps 
                SET last_scraped_at = NOW(), updated_at = NOW()
                WHERE id = $1
            """, app_id)
    
    async def record_scraping_metrics(self, app_id: int, platform: str,
                                    metrics: Dict[str, Any]) -> None:
        """
        Record scraping metrics for monitoring and analytics.
        
        Args:
            app_id: App ID
            platform: Platform ('apple' or 'google')
            metrics: Dictionary with metrics data
        """
        now = datetime.now()
        
        async with get_db_connection() as conn:
            await conn.execute("""
                INSERT INTO scraping_metrics (
                    app_id, platform, date, hour,
                    total_requests, successful_requests, failed_requests,
                    reviews_scraped, reviews_inserted, average_rating,
                    average_response_time_ms, total_duration_seconds,
                    rate_limit_hits, proxy_rotations
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (app_id, platform, date, hour) DO UPDATE SET
                    total_requests = scraping_metrics.total_requests + EXCLUDED.total_requests,
                    successful_requests = scraping_metrics.successful_requests + EXCLUDED.successful_requests,
                    failed_requests = scraping_metrics.failed_requests + EXCLUDED.failed_requests,
                    reviews_scraped = scraping_metrics.reviews_scraped + EXCLUDED.reviews_scraped,
                    reviews_inserted = scraping_metrics.reviews_inserted + EXCLUDED.reviews_inserted,
                    average_rating = (scraping_metrics.average_rating + EXCLUDED.average_rating) / 2,
                    average_response_time_ms = (scraping_metrics.average_response_time_ms + EXCLUDED.average_response_time_ms) / 2,
                    total_duration_seconds = scraping_metrics.total_duration_seconds + EXCLUDED.total_duration_seconds,
                    rate_limit_hits = scraping_metrics.rate_limit_hits + EXCLUDED.rate_limit_hits,
                    proxy_rotations = scraping_metrics.proxy_rotations + EXCLUDED.proxy_rotations
            """, 
                app_id, platform, now.date(), now.hour,
                metrics.get('total_requests', 0),
                metrics.get('successful_requests', 0),
                metrics.get('failed_requests', 0),
                metrics.get('reviews_scraped', 0),
                metrics.get('reviews_inserted', 0),
                metrics.get('average_rating', 0.0),
                metrics.get('average_response_time_ms', 0.0),
                metrics.get('total_duration_seconds', 0.0),
                metrics.get('rate_limit_hits', 0),
                metrics.get('proxy_rotations', 0)
            )
    
    async def get_app_by_internal_id(self, internal_app_id: str) -> Optional[Dict[str, Any]]:
        """Get app by internal app ID."""
        async with get_db_connection() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM apps WHERE internal_app_id = $1 AND is_active = true
            """, internal_app_id)
            
            return dict(row) if row else None
    
    async def get_scraping_job_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get scraping job statistics for the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dictionary with statistics
        """
        since = datetime.now() - timedelta(hours=hours)
        
        async with get_db_connection() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_jobs,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed_jobs,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed_jobs,
                    COUNT(*) FILTER (WHERE status = 'running') as running_jobs,
                    SUM(reviews_scraped) as total_reviews_scraped,
                    SUM(reviews_inserted) as total_reviews_inserted,
                    AVG(scraping_duration_seconds) as avg_scraping_duration,
                    AVG(insertion_duration_seconds) as avg_insertion_duration
                FROM scraping_jobs 
                WHERE started_at >= $1
            """, since)
            
            return dict(stats) if stats else {}
    
    async def get_app_performance_metrics(self, app_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get performance metrics for a specific app over time.
        
        Args:
            app_id: App ID
            days: Number of days to look back
            
        Returns:
            List of daily metrics
        """
        since = datetime.now().date() - timedelta(days=days)
        
        async with get_db_connection() as conn:
            rows = await conn.fetch("""
                SELECT 
                    date,
                    platform,
                    SUM(total_requests) as total_requests,
                    SUM(successful_requests) as successful_requests,
                    SUM(failed_requests) as failed_requests,
                    SUM(reviews_scraped) as reviews_scraped,
                    SUM(reviews_inserted) as reviews_inserted,
                    AVG(average_rating) as average_rating,
                    AVG(average_response_time_ms) as avg_response_time_ms,
                    SUM(rate_limit_hits) as rate_limit_hits
                FROM scraping_metrics 
                WHERE app_id = $1 AND date >= $2
                GROUP BY date, platform
                ORDER BY date DESC, platform
            """, app_id, since)
            
            return [dict(row) for row in rows]


# Singleton instance
app_management_service = AppManagementService()