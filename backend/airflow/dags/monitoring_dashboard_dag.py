import sys
import os
sys.path.insert(0, '/opt/airflow')
sys.path.insert(0, '/opt/airflow/backend')
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.models import Variable

from backend.services.app_management_service import AppManagementService
from backend.database import connection as db_connection

default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'email_on_failure': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

async def generate_daily_report(**context):
    """Generate daily scraping report"""
    logger = logging.getLogger("monitoring.daily_report")
    
    try:
        await db_connection.connect_to_db()
        app_service = AppManagementService()
        
        # Get yesterday's statistics
        stats = await app_service.get_scraping_job_stats(hours=24)
        
        # Get per-app performance
        async with get_db_connection() as conn:
            app_performance = await conn.fetch("""
                SELECT 
                    a.name,
                    a.internal_app_id,
                    COUNT(sj.id) as jobs_count,
                    SUM(sj.reviews_scraped) as total_scraped,
                    SUM(sj.reviews_inserted) as total_inserted,
                    AVG(sj.scraping_duration_seconds) as avg_duration,
                    COUNT(*) FILTER (WHERE sj.status = 'failed') as failed_jobs
                FROM apps a
                LEFT JOIN scraping_jobs sj ON a.id = sj.app_id 
                    AND sj.started_at >= NOW() - INTERVAL '24 hours'
                WHERE a.is_active = true
                GROUP BY a.id, a.name, a.internal_app_id
                ORDER BY total_scraped DESC NULLS LAST
            """)
        
        # Format report
        report = {
            'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'overall_stats': stats,
            'app_performance': [dict(row) for row in app_performance],
            'generated_at': datetime.now().isoformat()
        }
        
        logger.info("Daily report generated successfully")
        return report
        
    except Exception as e:
        logger.error(f"Failed to generate daily report: {e}")
        raise
    finally:
        await db_connection.close_db_connection()

def daily_report_task(**context):
    return asyncio.run(generate_daily_report(**context))

async def cleanup_old_data(**context):
    """Clean up old scraping jobs and metrics"""
    logger = logging.getLogger("monitoring.cleanup")
    
    try:
        await db_connection.connect_to_db()
        
        # Keep data for configurable number of days
        retention_days = int(Variable.get('DATA_RETENTION_DAYS', default_var='90'))
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        async with get_db_connection() as conn:
            # Clean up old scraping jobs
            deleted_jobs = await conn.fetchval("""
                DELETE FROM scraping_jobs 
                WHERE started_at < $1 AND status IN ('completed', 'failed', 'cancelled')
                RETURNING COUNT(*)
            """, cutoff_date)
            
            # Clean up old metrics (keep daily aggregates)
            deleted_metrics = await conn.fetchval("""
                DELETE FROM scraping_metrics 
                WHERE date < $1
                RETURNING COUNT(*)
            """, cutoff_date.date())
            
            # Clean up old reviews (optional, be careful with this)
            cleanup_reviews = Variable.get('CLEANUP_OLD_REVIEWS', default_var='false').lower() == 'true'
            deleted_reviews = 0
            
            if cleanup_reviews:
                review_retention_days = int(Variable.get('REVIEW_RETENTION_DAYS', default_var='365'))
                review_cutoff = datetime.now() - timedelta(days=review_retention_days)
                
                deleted_reviews = await conn.fetchval("""
                    DELETE FROM reviews 
                    WHERE created_at < $1
                    RETURNING COUNT(*)
                """, review_cutoff)
        
        cleanup_result = {
            'deleted_jobs': deleted_jobs or 0,
            'deleted_metrics': deleted_metrics or 0,
            'deleted_reviews': deleted_reviews,
            'retention_days': retention_days,
            'cutoff_date': cutoff_date.isoformat()
        }
        
        logger.info(f"Cleanup completed: {cleanup_result}")
        return cleanup_result
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise
    finally:
        await db_connection.close_db_connection()

def cleanup_task(**context):
    return asyncio.run(cleanup_old_data(**context))

async def health_check(**context):
    """Perform system health checks"""
    logger = logging.getLogger("monitoring.health_check")
    
    health_status = {
        'database': False,
        'active_apps': 0,
        'recent_jobs': 0,
        'failed_jobs_24h': 0,
        'avg_success_rate': 0.0,
        'status': 'unknown',
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        await db_connection.connect_to_db()
        health_status['database'] = True
        
        app_service = AppManagementService()
        
        # Check active apps
        active_apps = await app_service.get_active_apps()
        health_status['active_apps'] = len(active_apps)
        
        # Check recent job activity
        stats = await app_service.get_scraping_job_stats(hours=24)
        health_status['recent_jobs'] = stats.get('total_jobs', 0)
        health_status['failed_jobs_24h'] = stats.get('failed_jobs', 0)
        
        # Calculate success rate
        total_jobs = stats.get('total_jobs', 0)
        failed_jobs = stats.get('failed_jobs', 0)
        if total_jobs > 0:
            health_status['avg_success_rate'] = ((total_jobs - failed_jobs) / total_jobs) * 100
        
        # Determine overall status
        if health_status['avg_success_rate'] >= 95:
            health_status['status'] = 'healthy'
        elif health_status['avg_success_rate'] >= 80:
            health_status['status'] = 'warning'
        else:
            health_status['status'] = 'critical'
        
        logger.info(f"Health check completed: {health_status['status']}")
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_status['status'] = 'error'
        health_status['error'] = str(e)
        return health_status
    finally:
        await db_connection.close_db_connection()

def health_check_task(**context):
    return asyncio.run(health_check(**context))

async def generate_metrics_summary(**context):
    """Generate comprehensive metrics summary for monitoring dashboards"""
    logger = logging.getLogger("monitoring.metrics_summary")
    
    try:
        await db_connection.connect_to_db()
        
        async with get_db_connection() as conn:
            # Platform performance comparison
            platform_stats = await conn.fetch("""
                SELECT 
                    platform,
                    COUNT(*) as total_reviews,
                    AVG(rating) as avg_rating,
                    COUNT(DISTINCT app_id) as apps_count
                FROM reviews 
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY platform
            """)
            
            # Daily trends
            daily_trends = await conn.fetch("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as reviews_count,
                    AVG(rating) as avg_rating,
                    COUNT(DISTINCT app_id) as active_apps
                FROM reviews 
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
            
            # Top performing apps
            top_apps = await conn.fetch("""
                SELECT 
                    a.name,
                    a.internal_app_id,
                    COUNT(r.id) as review_count,
                    AVG(r.rating) as avg_rating,
                    MAX(r.created_at) as last_review
                FROM apps a
                JOIN reviews r ON a.internal_app_id = r.app_id
                WHERE r.created_at >= NOW() - INTERVAL '7 days'
                GROUP BY a.id, a.name, a.internal_app_id
                ORDER BY review_count DESC
                LIMIT 10
            """)
            
            # Error analysis
            error_analysis = await conn.fetch("""
                SELECT 
                    DATE(started_at) as date,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed_jobs,
                    COUNT(*) as total_jobs,
                    ROUND(
                        (COUNT(*) FILTER (WHERE status = 'failed')::decimal / COUNT(*)) * 100, 2
                    ) as failure_rate
                FROM scraping_jobs 
                WHERE started_at >= NOW() - INTERVAL '7 days'
                GROUP BY DATE(started_at)
                ORDER BY date DESC
            """)
        
        metrics_summary = {
            'platform_performance': [dict(row) for row in platform_stats],
            'daily_trends': [dict(row) for row in daily_trends],
            'top_apps': [dict(row) for row in top_apps],
            'error_analysis': [dict(row) for row in error_analysis],
            'generated_at': datetime.now().isoformat()
        }
        
        logger.info("Metrics summary generated successfully")
        return metrics_summary
        
    except Exception as e:
        logger.error(f"Failed to generate metrics summary: {e}")
        raise
    finally:
        await db_connection.close_db_connection()

def metrics_summary_task(**context):
    return asyncio.run(generate_metrics_summary(**context))

# Monitoring DAG
with DAG(
    dag_id='monitoring_dashboard',
    default_args=default_args,
    description='Monitoring and metrics dashboard for enterprise scraping',
    schedule='0 1 * * *',  # Daily at 1 AM
    start_date=datetime(2025, 5, 1),
    catchup=False,
    tags=['monitoring', 'metrics', 'dashboard', 'maintenance'],
    doc_md="""
    ## Monitoring Dashboard DAG
    
    This DAG provides comprehensive monitoring and maintenance for the Insight Aura.
    
    **Features:**
    - Daily performance reports
    - System health checks
    - Data cleanup and maintenance
    - Metrics aggregation for dashboards
    
    **Schedule:** Runs daily at 1 AM
    **Retention:** Configurable via Airflow Variables
    """
) as monitoring_dag:

    start_monitoring = EmptyOperator(
        task_id='start_monitoring',
        doc_md="Initialize monitoring and maintenance tasks"
    )

    # Health check
    health_check = PythonOperator(
        task_id='system_health_check',
        python_callable=health_check_task,
        doc_md="Perform comprehensive system health check"
    )

    # Generate daily report
    daily_report = PythonOperator(
        task_id='generate_daily_report',
        python_callable=daily_report_task,
        doc_md="Generate daily scraping performance report"
    )

    # Generate metrics summary
    metrics_summary = PythonOperator(
        task_id='generate_metrics_summary',
        python_callable=metrics_summary_task,
        doc_md="Generate comprehensive metrics for monitoring dashboards"
    )

    # Cleanup old data
    cleanup = PythonOperator(
        task_id='cleanup_old_data',
        python_callable=cleanup_task,
        doc_md="Clean up old scraping jobs and metrics based on retention policy"
    )

    # Send monitoring notifications
    def send_monitoring_report(**context):
        """Send monitoring report via notifications"""
        health_result = context['task_instance'].xcom_pull(task_ids='system_health_check')
        daily_report_result = context['task_instance'].xcom_pull(task_ids='generate_daily_report')
        cleanup_result = context['task_instance'].xcom_pull(task_ids='cleanup_old_data')
        
        if health_result and daily_report_result:
            status_emoji = {
                'healthy': '✅',
                'warning': '⚠️',
                'critical': '🚨',
                'error': '❌'
            }.get(health_result['status'], '❓')
            
            stats = daily_report_result.get('overall_stats', {})
            
            message = f"""
{status_emoji} **Daily System Report**

🏥 **Health Status:** {health_result['status'].upper()}
📊 **Active Apps:** {health_result['active_apps']}
📈 **Success Rate:** {health_result['avg_success_rate']:.1f}%

📋 **24h Activity:**
• Total Jobs: {stats.get('total_jobs', 0)}
• Completed: {stats.get('completed_jobs', 0)}
• Failed: {stats.get('failed_jobs', 0)}
• Reviews Scraped: {stats.get('total_reviews_scraped', 0)}
• Reviews Inserted: {stats.get('total_reviews_inserted', 0)}

🧹 **Maintenance:**
• Cleaned Jobs: {cleanup_result.get('deleted_jobs', 0)}
• Cleaned Metrics: {cleanup_result.get('deleted_metrics', 0)}

📅 **Report Date:** {daily_report_result['date']}
            """
            
            logger = logging.getLogger("monitoring.notifications")
            logger.info("Daily monitoring report generated")
            logger.info(message)

    monitoring_report = PythonOperator(
        task_id='send_monitoring_report',
        python_callable=send_monitoring_report,
        doc_md="Send comprehensive monitoring report via notifications"
    )

    end_monitoring = EmptyOperator(
        task_id='end_monitoring',
        doc_md="Complete monitoring and maintenance pipeline"
    )

    # Define dependencies
    start_monitoring >> [health_check, daily_report, metrics_summary]
    [health_check, daily_report, metrics_summary] >> cleanup >> monitoring_report >> end_monitoring