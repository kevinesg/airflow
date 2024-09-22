from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable
from helper_functions.alerts import send_slack_alert




DAG_NAME = 'cleanup__vscode_server'
DAG_DESCRIPTION = 'cleanup of .vscode-server folder and files'
TAGS = ['cleanup', 'vscode']
DAG_OWNER = 'kevinesg'
EMAIL = ['kevinlloydesguerra@gmail.com']
START_DATE = datetime(2023, 8, 22, 1)
CRON_SCHEDULE = '0 0 * * 0'
RETRY_DELAY = timedelta(minutes=2)
RETRIES = 5
MAX_ACTIVE_RUNS = 1
CONCURRENCY = 1

default_args = {
    'description': DAG_DESCRIPTION,
    'owner': DAG_OWNER,
    'retries': RETRIES,
    'retry_delay': RETRY_DELAY,
    'email_on_failure': True,
    'email_on_retry': False,
    'email': EMAIL
}


with DAG(
    dag_id=DAG_NAME,
    tags=TAGS,
    start_date=START_DATE,
    schedule_interval=CRON_SCHEDULE,
    max_active_runs=MAX_ACTIVE_RUNS,
    concurrency=CONCURRENCY,
    on_failure_callback=send_slack_alert,
    catchup=False,
    default_args=default_args
):
    _ = BashOperator(
        task_id="cleanup",
        bash_command="cd && rm -rf .vscode-server "
    )