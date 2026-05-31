from datetime import datetime

from airflow import DAG


with DAG(
    dag_id="demo_broken",
    start_date=datetime.now(),
    schedule="@daily",
    catchup=True,
):
    pass