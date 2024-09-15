from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.models import Variable




DAG_NAME = f'dbt__refresh_data_catalog'
DAG_DESCRIPTION = 'refresh dbt data catalog and elementary-data report'
TAGS = ['data quality', 'dbt docs']
DAG_OWNER = 'kevinesg'
EMAIL = ['kevinlloydesguerra@gmail.com']
START_DATE = datetime(2023, 8, 30, 8)
CRON_SCHEDULE = '30 * * * *'
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
    catchup=False,
    default_args=default_args
):

    generate_dbt_docs = BashOperator(
        task_id="generate_dbt_docs",
        bash_command=f" \
            cd {Variable.get('dir__dbt')}/data_warehouse && \
            conda run -n dbt \
            dbt compile --target=prod && \
            conda run -n dbt \
            dbt docs generate --target=prod --no-compile && \
            cd {Variable.get('dir__scripts')} && \
            conda run -n scripts-misc \
            python misc/combine_dbt_data_catalog_files.py \
                --dir={Variable.get('dir__dbt')}/data_warehouse "
    )

    generate_dbt_docs