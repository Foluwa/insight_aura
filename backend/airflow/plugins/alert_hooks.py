from airflow.models import TaskInstance
from airflow.utils.state import State
from backend.api.utils.notification import (
    send_telegram_alert,
    send_slack_alert,
    send_email_alert
)

def failure_alert_callback(context):
    task_instance: TaskInstance = context.get("task_instance")
    dag_id = context.get("dag").dag_id
    task_id = task_instance.task_id
    error = context.get("exception")

    message = f"""
❌ Airflow Task Failed
DAG: {dag_id}
Task: {task_id}
Error: {str(error)}
"""

    send_telegram_alert(message)
    send_slack_alert(message)
    send_email_alert(
        subject=f"❌ Airflow Task Failed — {dag_id}.{task_id}",
        body=message,
        to="you@example.com"
    )