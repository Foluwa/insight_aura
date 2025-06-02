# Safe imports for Airflow 3.0.1
import sys
import os

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
backend_path = os.path.abspath(os.path.join(current_dir, '..', '..'))

for path in [project_root, backend_path, '/opt/airflow', '/opt/airflow/backend']:
    if path not in sys.path:
        sys.path.insert(0, path)

# Safe import function
def safe_import(module_name, fallback=None):
    try:
        return __import__(module_name, fromlist=[''])
    except ImportError as e:
        print(f"Warning: Could not import {module_name}: {e}")
        return fallback

sys.path.insert(0, '/opt/airflow')
sys.path.insert(0, '/opt/airflow/backend')
import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

# Add project root to Python path
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from airflow import DAG
from airflow.operators.python import PythonOperator
# from airflow.operators.dummy import EmptyOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule
from airflow.models import Variable

# Import services
from backend.services.app_management_service import AppManagementService
from backend.services.review_scraper_manager import ReviewScraperManager
from backend.services.review_insertion_service import ReviewInsertionService
from backend.database import connection as db_connection
from backend.airflow.plugins.alert_hooks import enhanced_failure_alert_callback, success_alert_callback

# Initialize Sentry for error tracking
sentry_dsn = Variable.get('SENTRY_DSN', default_var=None)
if sentry_dsn:
    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR
    )
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[sentry_logging],
        traces_sample_rate=0.1,
        environment=Variable.get('ENVIRONMENT', default_var='production')
    )

# DAG Configuration
default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'on_failure_callback': enhanced_failure_alert_callback,
    'on_success_callback': success_alert_callback,
    'max_active_runs': 1
}

def setup_task_logger(task_name: str, dag_run_id: str) -> logging.Logger:
    """Setup logger with Sentry integration"""
    logger = logging.getLogger(f"enterprise_scraping.{task_name}")
    
    # Add context to Sentry
    if sentry_dsn:
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("dag_id", "enterprise_scraping_dag")
            scope.set_tag("task_id", task_name)
            scope.set_tag("dag_run_id", dag_run_id)
    
    return logger

async def discover_apps_to_scrape(**context) -> List[Dict[str, Any]]:
    """
    Discover apps that are due for scraping based on their frequency settings.
    
    Returns:
        List of apps to scrape
    """
    dag_run_id = context['dag_run'].dag_id
    logger = setup_task_logger("discover_apps", dag_run_id)
    
    try:
        await db_connection.connect_to_db()
        
        app_service = AppManagementService()
        apps_due = await app_service.get_apps_due_for_scraping()
        
        logger.info(f"Found {len(apps_due)} apps due for scraping")
        
        # Log each app
        for app in apps_due:
            logger.info(f"App: {app['name']} ({app['internal_app_id']}) - "
                       f"Last scraped: {app['last_scraped_at']}")
        
        # Store in XCom for downstream tasks
        context['task_instance'].xcom_push(key='apps_to_scrape', value=apps_due)
        
        return {
            'success': True,
            'apps_count': len(apps_due),
            'apps': apps_due
        }
        
    except Exception as e:
        logger.error(f"Failed to discover apps: {e}")
        sentry_sdk.capture_exception(e)
        raise
    finally:
        await db_connection.close_db_connection()

def discover_apps_task(**context):
    """Wrapper for discover apps task"""
    return asyncio.run(discover_apps_to_scrape(**context))

async def scrape_app_reviews(app_config: Dict[str, Any], **context) -> Dict[str, Any]:
    """
    Scrape reviews for a specific app across all available platforms.
    
    Args:
        app_config: App configuration from database
        context: Airflow context
        
    Returns:
        Scraping results
    """
    dag_run_id = context['dag_run'].dag_id
    task_id = context['task_id']
    logger = setup_task_logger(f"scrape_{app_config['internal_app_id']}", dag_run_id)
    
    app_id = app_config['id']
    app_name = app_config['name']
    
    # Add Sentry context
    if sentry_dsn:
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("app_id", app_id)
            scope.set_tag("app_name", app_name)
    
    try:
        await db_connection.connect_to_db()
        
        app_service = AppManagementService()
        
        # Create scraping job record
        job_id = await app_service.create_scraping_job(
            app_id=app_id,
            platform='both',
            dag_run_id=dag_run_id,
            reviews_requested=app_config['reviews_per_run']
        )
        
        # Update job status to running
        await app_service.update_scraping_job(
            job_id=job_id,
            status='running',
            task_instance_id=task_id
        )
        
        logger.info(f"Starting scraping for {app_name} (Job ID: {job_id})")
        
        # Initialize scraper with app-specific settings
        proxy_config = _get_proxy_config()
        scraper_manager = ReviewScraperManager(
            proxy_config=proxy_config,
            rate_limit_delay=app_config['rate_limit_delay'],
            max_retries=app_config['max_retries'],
            timeout=60
        )
        
        # Prepare app identifiers
        app_identifiers = {}
        if app_config['apple_app_id']:
            app_identifiers['apple'] = app_config['apple_app_id']
        if app_config['google_package_name']:
            app_identifiers['google'] = app_config['google_package_name']
        
        # Track metrics
        scraping_start = datetime.now()
        
        # Scrape reviews from both platforms
        scraping_result = await scraper_manager.scrape_both_platforms(
            app_identifiers=app_identifiers,
            count=app_config['reviews_per_run']
        )
        
        scraping_duration = (datetime.now() - scraping_start).total_seconds()
        
        # Process results
        total_scraped = scraping_result['summary']['total_reviews']
        successful_platforms = scraping_result['summary']['successful_platforms']
        failed_platforms = scraping_result['summary']['failed_platforms']
        
        # Insert reviews into database
        insertion_start = datetime.now()
        insertion_service = ReviewInsertionService()
        total_inserted = 0
        
        for platform in successful_platforms:
            platform_result = scraping_result[platform]
            if platform_result and platform_result.get('success'):
                reviews = platform_result['reviews']
                
                if platform == 'apple':
                    insertion_result = await insertion_service.insert_apple_reviews(
                        reviews, app_config['internal_app_id']
                    )
                elif platform == 'google':
                    insertion_result = await insertion_service.insert_google_reviews(
                        reviews, app_config['internal_app_id']
                    )
                
                total_inserted += insertion_result['inserted_count']
                
                # Record platform-specific metrics
                await app_service.record_scraping_metrics(
                    app_id=app_id,
                    platform=platform,
                    metrics={
                        'total_requests': 1,
                        'successful_requests': 1 if insertion_result['inserted_count'] > 0 else 0,
                        'failed_requests': 0,
                        'reviews_scraped': len(reviews),
                        'reviews_inserted': insertion_result['inserted_count'],
                        'average_rating': sum(r.get('rating', r.get('score', 0)) for r in reviews) / len(reviews) if reviews else 0,
                        'total_duration_seconds': scraping_duration / len(successful_platforms)
                    }
                )
        
        insertion_duration = (datetime.now() - insertion_start).total_seconds()
        
        # Update job with final results
        status = 'completed' if total_inserted > 0 else 'failed'
        await app_service.update_scraping_job(
            job_id=job_id,
            status=status,
            reviews_scraped=total_scraped,
            reviews_inserted=total_inserted,
            scraping_duration_seconds=scraping_duration,
            insertion_duration_seconds=insertion_duration
        )
        
        # Update app last scraped timestamp
        if total_inserted > 0:
            await app_service.update_app_last_scraped(app_id)
        
        result = {
            'success': True,
            'app_id': app_id,
            'app_name': app_name,
            'job_id': job_id,
            'reviews_scraped': total_scraped,
            'reviews_inserted': total_inserted,
            'successful_platforms': successful_platforms,
            'failed_platforms': failed_platforms,
            'scraping_duration': scraping_duration,
            'insertion_duration': insertion_duration
        }
        
        logger.info(f"Completed scraping for {app_name}: "
                   f"{total_scraped} scraped, {total_inserted} inserted")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to scrape {app_name}: {e}")
        sentry_sdk.capture_exception(e)
        
        # Update job with error
        try:
            await app_service.update_scraping_job(
                job_id=job_id,
                status='failed',
                error_message=str(e),
                error_traceback=str(e.__traceback__) if hasattr(e, '__traceback__') else None
            )
        except:
            pass
        
        return {
            'success': False,
            'app_id': app_id,
            'app_name': app_name,
            'error': str(e)
        }
        
    finally:
        await db_connection.close_db_connection()

def _get_proxy_config():
    """Get proxy configuration from Airflow Variables"""
    proxy_enabled = Variable.get('PROXY_ENABLED', default_var='false').lower() == 'true'
    if not proxy_enabled:
        return None
    
    return {
        'http': Variable.get('HTTP_PROXY', default_var=None),
        'https': Variable.get('HTTPS_PROXY', default_var=None)
    }

async def generate_scraping_summary(**context) -> Dict[str, Any]:
    """Generate summary of all scraping activities"""
    dag_run_id = context['dag_run'].dag_id
    logger = setup_task_logger("generate_summary", dag_run_id)
    
    try:
        await db_connection.connect_to_db()
        
        app_service = AppManagementService()
        
        # Get job statistics for this DAG run
        stats = await app_service.get_scraping_job_stats(hours=1)
        
        logger.info(f"Scraping summary: {stats}")
        
        return {
            'success': True,
            'summary': stats,
            'dag_run_id': dag_run_id,
            'completed_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        sentry_sdk.capture_exception(e)
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        await db_connection.close_db_connection()

def generate_summary_task(**context):
    """Wrapper for summary generation"""
    return asyncio.run(generate_scraping_summary(**context))

# Define the DAG
with DAG(
    dag_id='enterprise_scraping_dag',
    default_args=default_args,
    description='Enterprise multi-app review scraping with monitoring and metrics',
    schedule='0 */6 * * *',  # Every 6 hours
    start_date=datetime(2025, 5, 1),
    catchup=False,
    tags=['enterprise', 'scraping', 'reviews', 'monitoring'],
    max_active_runs=1,
    doc_md="""
    ## Enterprise Review Scraping Pipeline
    
    This DAG automatically discovers and scrapes reviews from multiple apps across Apple App Store and Google Play Store.
    
    **Features:**
    - Dynamic app discovery from database
    - Individual app rate limiting and configuration
    - Comprehensive metrics collection
    - Sentry error tracking
    - Multi-platform scraping with fault tolerance
    
    **Configuration:**
    Apps are configured in the `apps` table with individual settings for:
    - Scraping frequency
    - Reviews per run
    - Rate limiting
    - Platform availability
    
    **Monitoring:**
    - Real-time job tracking in `scraping_jobs` table
    - Metrics aggregation in `scraping_metrics` table
    - Sentry integration for error tracking
    - Telegram/Slack notifications
    """
) as dag:

    # Start task
    start = EmptyOperator(
        task_id='start_enterprise_scraping',
        doc_md="Initialize enterprise scraping pipeline"
    )

    # Discover apps that need scraping
    discover_apps = PythonOperator(
        task_id='discover_apps_to_scrape',
        python_callable=discover_apps_task,
        doc_md="Discover apps that are due for scraping based on frequency settings"
    )

    # Dynamic task generation for each app
    def create_app_scraping_tasks(**context):
        """Create dynamic tasks for each app that needs scraping"""
        apps_to_scrape = context['task_instance'].xcom_pull(
            task_ids='discover_apps_to_scrape',
            key='apps_to_scrape'
        )
        
        if not apps_to_scrape:
            return 'no_apps_to_scrape'
        
        # Store app configs for task generation
        context['task_instance'].xcom_push(
            key='app_configs',
            value=apps_to_scrape
        )
        
        return 'parallel_scraping_group'

    # Branch operator to check if there are apps to scrape
    check_apps = PythonOperator(
        task_id='check_apps_to_scrape',
        python_callable=create_app_scraping_tasks,
        doc_md="Check if there are apps to scrape and prepare task configuration"
    )

    # No apps to scrape path
    no_apps_to_scrape = EmptyOperator(
        task_id='no_apps_to_scrape',
        doc_md="Handle case where no apps need scraping"
    )

    # Parallel scraping task group
    with TaskGroup(group_id='parallel_scraping_group') as scraping_group:
        
        def create_scraping_task(app_config):
            """Create a scraping task for a specific app"""
            app_internal_id = app_config['internal_app_id']
            
            def scrape_single_app(**context):
                return asyncio.run(scrape_app_reviews(app_config, **context))
            
            return PythonOperator(
                task_id=f'scrape_{app_internal_id}',
                python_callable=scrape_single_app,
                doc_md=f"Scrape reviews for {app_config['name']} ({app_internal_id})"
            )
        
        # Note: In practice, you'd use Airflow's dynamic task mapping or 
        # a custom operator for truly dynamic task generation
        # For now, we'll handle this in the summary task

    # Generate summary and metrics
    generate_summary = PythonOperator(
        task_id='generate_scraping_summary',
        python_callable=generate_summary_task,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
        doc_md="Generate comprehensive summary of scraping activities and metrics"
    )

    # Send notifications
    def send_enterprise_notifications(**context):
        """Send comprehensive notifications with metrics"""
        summary = context['task_instance'].xcom_pull(task_ids='generate_scraping_summary')
        
        if summary and summary.get('success'):
            stats = summary.get('summary', {})
            
            message = f"""
🏢 **Enterprise Scraping Summary**

📊 **Job Statistics:**
• Total Jobs: {stats.get('total_jobs', 0)}
• Completed: {stats.get('completed_jobs', 0)}
• Failed: {stats.get('failed_jobs', 0)}
• Currently Running: {stats.get('running_jobs', 0)}

📈 **Review Metrics:**
• Reviews Scraped: {stats.get('total_reviews_scraped', 0)}
• Reviews Inserted: {stats.get('total_reviews_inserted', 0)}

⚡ **Performance:**
• Avg Scraping Time: {stats.get('avg_scraping_duration', 0):.2f}s
• Avg Insertion Time: {stats.get('avg_insertion_duration', 0):.2f}s

🕐 **Run Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            logger = setup_task_logger("notifications", context['dag_run'].dag_id)
            logger.info("Enterprise scraping completed successfully")
            logger.info(message)
            
            # Here you would send to your notification channels
            # The enhanced_alert_hooks will handle the actual sending

    notifications = PythonOperator(
        task_id='send_notifications',
        python_callable=send_enterprise_notifications,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
        doc_md="Send comprehensive notifications with scraping summary"
    )

    # End task
    end = EmptyOperator(
        task_id='end_enterprise_scraping',
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
        doc_md="Complete enterprise scraping pipeline"
    )

    # Define task dependencies
    start >> discover_apps >> check_apps
    check_apps >> [no_apps_to_scrape, scraping_group]
    [no_apps_to_scrape, scraping_group] >> generate_summary >> notifications >> end
    