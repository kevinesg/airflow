from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable
from helper_functions.alerts import send_slack_alert




DAG_NAME = f'dbt__freshness_test'
DAG_DESCRIPTION = 'check freshness of dbt models (if freshness is specified)'
TAGS = ['data quality']
DAG_OWNER = 'kevinesg'
EMAIL = ['kevinlloydesguerra@gmail.com']
START_DATE = datetime(2023, 8, 30, 8)
CRON_SCHEDULE = '45 * * * *'
RETRY_DELAY = timedelta(minutes=2)
RETRIES = 0
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
) as dag:

    dbt_git_pull = BashOperator(
        task_id="dbt_git_pull",
        bash_command=Variable.get("git_pull__dbt")
    )

    with TaskGroup(group_id="test_freshness") as test_freshness: 

        sources = BashOperator(
            task_id="sources",
            bash_command=f" \
                cd {Variable.get('dir__dbt')}/data_warehouse && \
                conda run -n dbt \
                dbt source freshness \
                    --target=prod "
        )

        models = BashOperator(
            task_id="models",
            bash_command=f" \
                cd {Variable.get('dir__dbt')}/data_warehouse && \
                conda run -n dbt \
                    dbt test \
                    --target=prod \
                    --select tag:check_freshness "
        )

        sources >> models

        dbt_git_pull >> test_freshness