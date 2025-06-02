from airflow.models import TaskInstance
from airflow.utils.state import State

def failure_alert_callback(context):
    """Basic failure alert callback"""
    task_instance: TaskInstance = context.get("task_instance")
    dag_id = context.get("dag").dag_id
    task_id = task_instance.task_id
    error = context.get("exception")
    
    print(f"❌ Task failed: {dag_id}.{task_id} - Error: {str(error)}")

def enhanced_failure_alert_callback(context):
    """Enhanced failure alert callback - alias for backward compatibility"""
    return failure_alert_callback(context)

def success_alert_callback(context):
    """Basic success alert callback"""
    task_instance: TaskInstance = context.get("task_instance")
    dag_id = context.get("dag").dag_id
    task_id = task_instance.task_id
    
    print(f"✅ Task succeeded: {dag_id}.{task_id}")

# Backward compatibility
enhanced_failure_alert_callback = failure_alert_callback
