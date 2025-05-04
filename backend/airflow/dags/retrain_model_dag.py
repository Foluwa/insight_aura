import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.services.retrain_model import retrain_sentiment_model
from backend.airflow.plugins.alert_hooks import failure_alert_callback

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
    'on_failure_callback': failure_alert_callback,
}

with DAG(
    dag_id='retrain_sentiment_model',
    default_args=default_args,
    schedule_interval='@daily',  # Retrain daily if eligible
    start_date=datetime(2025, 5, 1),
    catchup=False,
    tags=['ml']
) as dag:

    retrain = PythonOperator(
        task_id='retrain_model',
        python_callable=retrain_sentiment_model
    )
