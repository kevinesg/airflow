from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable
from helper_functions.alerts import send_slack_alert




DAG_NAME = f'etl__OpenWeather'
DAG_DESCRIPTION = 'extracts data from OpenWeather API to create historical weather database for my location'
TAGS = ['openweather']
DAG_OWNER = 'kevinesg'
EMAIL = ['kevinlloydesguerra@gmail.com']
START_DATE = datetime(2023, 8, 22, 1)
CRON_SCHEDULE = '0 1 * * *'
RETRY_DELAY = timedelta(minutes=5)
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

    git_pull = TaskGroup(group_id="git_pull")

    dbt_git_pull = BashOperator(
        task_id="dbt_git_pull",
        bash_command=Variable.get("git_pull__dbt"),
        task_group=git_pull
    )

    scripts_git_pull = BashOperator(
        task_id="scripts_git_pull",
        bash_command=Variable.get("git_pull__scripts"),
        task_group=git_pull
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f" \
            cd {Variable.get('dir__dbt')}/data_warehouse && \
            conda run -n dbt \
            dbt build \
                --target prod \
                --select source:openweather+ \
                --exclude tag:check_freshness "
    )

    with TaskGroup(group_id="ingest_data") as ingest_data:
        extract = BashOperator(
            task_id="extract",
            bash_command=f" \
                cd {Variable.get('dir__scripts')} && \
                conda run -n scripts-batch \
                python etl/batch/openweather.py \
                --step=extract "
        )

        extract

        git_pull >> ingest_data >> dbt_build