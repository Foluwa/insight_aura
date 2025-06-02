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

# This DAG can be triggered manually with configuration to scrape specific apps.
# """

# from datetime import datetime, timedelta
# from airflow import DAG
# from airflow.operators.python import PythonOperator
# from airflow.operators.dummy import DummyOperator
# from airflow.utils.trigger_rule import TriggerRule

# from backend.services.app_management_service import AppManagementService
# from backend.database import connection as db_connection


# def setup_task_logger(task_name: str, dag_run_id: str) -> logging.Logger:
#     """Setup logger with Sentry integration"""
#     logger = logging.getLogger(f"enterprise_scraping.{task_name}")
    
#     # Add context to Sentry
#     if sentry_dsn:
#         with sentry_sdk.configure_scope() as scope:
#             scope.set_tag("dag_id", "enterprise_scraping_dag")
#             scope.set_tag("task_id", task_name)
#             scope.set_tag("dag_run_id", dag_run_id)
    
#     return logger

# def manual_scrape_app(**context):
#     """
#     Manually scrape a specific app based on DAG configuration.
    
#     Expected conf format:
#     {
#         "app_internal_id": "slack",
#         "reviews_count": 200,
#         "platforms": ["apple", "google"]  # or ["apple"] or ["google"]
#     }
#     """
#     import asyncio
    
#     # Get configuration from DAG run
#     conf = context['dag_run'].conf or {}
#     app_internal_id = conf.get('app_internal_id')
#     reviews_count = conf.get('reviews_count', 100)
#     platforms = conf.get('platforms', ['apple', 'google'])
    
#     if not app_internal_id:
#         raise ValueError("app_internal_id must be provided in DAG configuration")
    
#     logger = setup_task_logger("manual_scrape", context['dag_run'].dag_id)
#     logger.info(f"Manual scraping triggered for app: {app_internal_id}")
    
#     async def run_manual_scrape():
#         await db_connection.connect_to_db()
        
#         try:
#             app_service = AppManagementService()
            
#             # Get app configuration
#             app_config = await app_service.get_app_by_internal_id(app_internal_id)
#             if not app_config:
#                 raise ValueError(f"App not found: {app_internal_id}")
            
#             # Override reviews count
#             app_config['reviews_per_run'] = reviews_count
            
#             # Filter platforms
#             app_identifiers = {}
#             if 'apple' in platforms and app_config['apple_app_id']:
#                 app_identifiers['apple'] = app_config['apple_app_id']
#             if 'google' in platforms and app_config['google_package_name']:
#                 app_identifiers['google'] = app_config['google_package_name']
            
#             if not app_identifiers:
#                 raise ValueError("No valid platforms found for this app")
            
#             # Run scraping
#             result = await scrape_app_reviews(app_config, **context)
#             return result
            
#         finally:
#             await db_connection.close_db_connection()
    
#     return asyncio.run(run_manual_scrape())

# # Manual scraping DAG
# manual_dag = DAG(
#     dag_id='manual_app_scraping',
#     default_args={
#         'owner': 'data_team',
#         'retries': 1,
#         'retry_delay': timedelta(minutes=5),
#         'on_failure_callback': enhanced_failure_alert_callback,
#     },
#     description='Manual app scraping with custom configuration',
#     schedule=None,  # Manual trigger only
#     start_date=datetime(2025, 5, 1),
#     catchup=False,
#     tags=['manual', 'scraping', 'on-demand'],
#     doc_md="""
#     ## Manual App Scraping
    
#     This DAG allows manual scraping of specific apps with custom configuration.
    
#     **Usage:**
#     Trigger with configuration JSON:
#     ```json
#     {
#         "app_internal_id": "slack",
#         "reviews_count": 200,
#         "platforms": ["apple", "google"]
#     }
#     ```
    
#     **Parameters:**
#     - `app_internal_id`: Internal app identifier from apps table
#     - `reviews_count`: Number of reviews to scrape (optional, default: 100)
#     - `platforms`: List of platforms to scrape (optional, default: ["apple", "google"])
#     """
# )

# with manual_dag:
#     start_manual = DummyOperator(task_id='start_manual_scraping')
    
#     manual_scrape = PythonOperator(
#         task_id='manual_scrape_app',
#         python_callable=manual_scrape_app
#     )
    
#     end_manual = DummyOperator(task_id='end_manual_scraping')
    
#     start_manual >> manual_scrape >> end_manual