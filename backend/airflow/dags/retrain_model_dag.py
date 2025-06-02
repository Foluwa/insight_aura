
import sys
import os
sys.path.insert(0, '/opt/airflow')
sys.path.insert(0, '/opt/airflow/backend')
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

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
    schedule='@daily',  # Retrain daily if eligible
    start_date=datetime(2025, 5, 1),
    catchup=False,
    tags=['ml']
) as dag:

    retrain = PythonOperator(
        task_id='retrain_model',
        python_callable=retrain_sentiment_model
    )


# # Safe imports for Airflow 3.0.1
# import sys
# import os

# # Add project root to Python path
# current_dir = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
# backend_path = os.path.abspath(os.path.join(current_dir, '..', '..'))

# for path in [project_root, backend_path, '/opt/airflow', '/opt/airflow/backend']:
#     if path not in sys.path:
#         sys.path.insert(0, path)

# # Safe import function
# def safe_import(module_name, fallback=None):
#     try:
#         return __import__(module_name, fromlist=[''])
#     except ImportError as e:
#         print(f"Warning: Could not import {module_name}: {e}")
#         return fallback

# from airflow import DAG
# from airflow.operators.python import PythonOperator
# from datetime import datetime, timedelta
# from backend.services.retrain_model import retrain_sentiment_model
# from backend.airflow.plugins.alert_hooks import failure_alert_callback

# default_args = {
#     'owner': 'airflow',
#     'retries': 2,
#     'retry_delay': timedelta(minutes=10),
#     'on_failure_callback': failure_alert_callback,
# }

# # FIXED: schedule -> schedule for Airflow 3.0.1
# with DAG(
#     dag_id='retrain_sentiment_model',
#     default_args=default_args,
#     schedule='@daily',  # Retrain daily if eligible
#     start_date=datetime(2025, 5, 1),
#     catchup=False,
#     tags=['ml']
# ) as dag:

#     retrain = PythonOperator(
#         task_id='retrain_model',
#         python_callable=retrain_sentiment_model
#     )

