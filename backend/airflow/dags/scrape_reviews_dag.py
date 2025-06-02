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

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

from backend.services.google_review_scraper import scrape_google_reviews
from backend.services.apple_review_scraper import scrape_apple_reviews
from backend.airflow.plugins.alert_hooks import failure_alert_callback

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'on_failure_callback': failure_alert_callback
}

with DAG(
    dag_id='scrape_reviews_dag',
    default_args=default_args,
    schedule='0 */6 * * *',  # Every 6 hours
    start_date=datetime(2025, 5, 1),
    catchup=False,
    tags=['scraper']
) as dag:

    scrape_google = PythonOperator(
        task_id='scrape_google_play',
        python_callable=scrape_google_reviews
    )

    scrape_apple = PythonOperator(
        task_id='scrape_apple_store',
        python_callable=scrape_apple_reviews
    )

    scrape_google >> scrape_apple
