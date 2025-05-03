from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import asyncio
import logging

# Import your scraper functions
from backend.services.apple_scraper_service import scrape_apple_reviews
from backend.services.google_scraper_service import scrape_google_reviews

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': ['alerts@yourdomain.com'],
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=10),
}

# Define the DAG
with DAG(
    dag_id='scrape_reviews_dag',
    default_args=default_args,
    description='Daily scraping of app reviews from Apple and Google Play Stores',
    schedule_interval='@daily',
    start_date=datetime(2025, 4, 28),
    catchup=False,
    tags=['scraping', 'reviews'],
) as dag:

    def scrape_apple():
        app_ids = [123456789, 987654321]  # Replace with dynamic retrieval if needed
        for app_id in app_ids:
            try:
                asyncio.run(scrape_apple_reviews(app_id))
            except Exception as e:
                logger.error(f"Error scraping Apple app ID {app_id}: {e}")

    def scrape_google():
        app_ids = ['com.slack']  # Replace with dynamic retrieval if needed
        for app_id in app_ids:
            try:
                asyncio.run(scrape_google_reviews(app_id))
            except Exception as e:
                logger.error(f"Error scraping Google app ID {app_id}: {e}")

    scrape_apple_task = PythonOperator(
        task_id='scrape_apple_reviews',
        python_callable=scrape_apple,
    )

    scrape_google_task = PythonOperator(
        task_id='scrape_google_reviews',
        python_callable=scrape_google,
    )

    scrape_apple_task >> scrape_google_task
