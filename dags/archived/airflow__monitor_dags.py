import datetime as dt
import pytz
import numpy as np
import pandas as pd
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.task_group import TaskGroup
from airflow.utils.dates import days_ago
from airflow.models import Variable, DagRun
from sqlalchemy import create_engine, func, case
from sqlalchemy.orm import sessionmaker
#from scripts.python import alerts



DATABASE_URI = 'postgresql+psycopg2://airflow_user:airflow_pass@localhost/airflow_db'

def gather_dag_statistics():
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()

    now = dt.datetime.now(pytz.timezone('Asia/Manila'))
    past_7_days = now - dt.timedelta(days=7)
    past_30_days = now - dt.timedelta(days=30)

    # Query to get DAG run statistics
    dag_stats_query = session.query(
        DagRun.dag_id,
        func.count(DagRun.dag_id).label('total_runs'),
        func.avg(func.extract('epoch', DagRun.end_date) - func.extract('epoch', DagRun.start_date)).label('avg_run_time'),
        func.sum(case([(DagRun.state == 'failed', 1)], else_=0)).label('failed_runs'),
        func.sum(case([(DagRun.state == 'failed', func.extract('epoch', DagRun.end_date) - func.extract('epoch', DagRun.start_date))], else_=0)).label('total_failed_time')
    ).group_by(DagRun.dag_id).all()

    # Convert query results to DataFrame
    dag_stats_df = pd.DataFrame(dag_stats_query, columns=['dag_id', 'total_runs', 'avg_run_time', 'failed_runs', 'total_failed_time'])

    # Query to get counts for the past 7 and 30 days
    for days, label in [(7, '7_days'), (30, '30_days')]:
        start_date = now - dt.timedelta(days=days)
        count_query = session.query(
            DagRun.dag_id,
            func.count(DagRun.dag_id).label(f'total_runs_{label}'),
            func.sum(case([(DagRun.state == 'failed', 1)], else_=0)).label(f'failed_runs_{label}')
        ).filter(DagRun.execution_date >= start_date).group_by(DagRun.dag_id).all()
        count_df = pd.DataFrame(count_query, columns=['dag_id', f'total_runs_{label}', f'failed_runs_{label}'])
        dag_stats_df = pd.merge(dag_stats_df, count_df, on='dag_id', how='left')

    # Calculate percentages and average failed time
    dag_stats_df['failed_runs_7_days_percent'] = (dag_stats_df['failed_runs_7_days'] / dag_stats_df['total_runs_7_days'] * 100).fillna(0)
    dag_stats_df['failed_runs_30_days_percent'] = (dag_stats_df['failed_runs_30_days'] / dag_stats_df['total_runs_30_days'] * 100).fillna(0)
    dag_stats_df['avg_failed_time_minutes'] = (dag_stats_df['total_failed_time'].astype(float) / 60 / dag_stats_df['failed_runs'].replace(0, np.nan)).fillna(0)

    # Format the average run time to a more readable format
    #dag_stats_df['avg_run_time'] = pd.to_timedelta(dag_stats_df['avg_run_time'], unit='s')

    # Output results
    for col in dag_stats_df.columns[1:]:
        dag_stats_df[col] = round(dag_stats_df[col].astype(float).replace(np.nan, 0), 0).astype(int) # replace nulls with 0 and convert to integer
    results = dag_stats_df.to_dict(orient='records')
    print(dag_stats_df)
    for result in results:
        print(result)

    session.close()

    
DAG_NAME = 'airflow__monitor_dags'
DAG_DESCRIPTION = 'monitoring of airflow DAGs'
DAG_OWNER = 'kevinesg'
EMAIL = ['kevinlloydesguerra@gmail.com']
START_DATE = dt.datetime(2023, 8, 22, 1)
CRON_SCHEDULE = '0 0 * * *'
RETRY_DELAY = dt.timedelta(minutes=2)
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
    start_date=START_DATE,
    schedule_interval=CRON_SCHEDULE,
    max_active_runs=MAX_ACTIVE_RUNS,
    concurrency=CONCURRENCY,
    #on_failure_callback=alerts.task_fail_gchat_alert,
    catchup=False,
    default_args=default_args,
    tags=['metadata', 'airflow']
):
    _ = PythonOperator(
        task_id='get_dag_stats',
        python_callable=gather_dag_statistics
    )