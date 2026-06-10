from datetime import timedelta

import pendulum

from airflow import DAG
from airflow.operators.bash import BashOperator


PROJECT_DIR = "/opt/airflow/project"
CONFIG = "configs/variant_06.yml"
PERIOD_DATE = "{{ data_interval_start | ds }}"
PERIOD_END = "{{ data_interval_end | ds }}"
RAW_PATH = f"data/raw/variant_06/raw_{PERIOD_DATE}.json"
NORMALIZED_PATH = f"data/normalized/variant_06/normalized_{PERIOD_DATE}.csv"
MART_PATH = f"data/mart/variant_06/mart_{PERIOD_DATE}.csv"


with DAG(
    dag_id="etl_variant_06",
    start_date=pendulum.datetime(2024, 5, 1, tz="UTC"),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=1),
    },
    tags=["etl", "variant_06", "open_meteo"],
):

    extract = BashOperator(
        task_id="extract",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            f"echo '[INFO] data interval: {PERIOD_DATE} -> {PERIOD_END}' && "
            f"python src/pipeline/extract.py --config {CONFIG} "
            f"--start-date '{PERIOD_DATE}' --end-date '{PERIOD_DATE}' "
            f"--output-path '{RAW_PATH}'"
        ),
    )

    transform = BashOperator(
        task_id="transform",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            f"echo '[INFO] data interval: {PERIOD_DATE} -> {PERIOD_END}' && "
            f"python src/pipeline/normalize.py --config {CONFIG} "
            f"--raw-path '{RAW_PATH}' --output-path '{NORMALIZED_PATH}' && "
            f"python src/pipeline/mart.py --config {CONFIG} "
            f"--normalized-path '{NORMALIZED_PATH}' --output-path '{MART_PATH}'"
        ),
    )

    load = BashOperator(
        task_id="load",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            f"echo '[INFO] data interval: {PERIOD_DATE} -> {PERIOD_END}' && "
            "POSTGRES_HOST=postgres "
            "POSTGRES_PORT=5432 "
            "POSTGRES_DB=analytics "
            "POSTGRES_USER=student "
            "POSTGRES_PASSWORD=student_pw "
            f"python src/pipeline/load.py --config {CONFIG} "
            f"--mart-path '{MART_PATH}' --mode incremental"
        ),
    )

    dq = BashOperator(
        task_id="dq",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            f"echo '[INFO] data interval: {PERIOD_DATE} -> {PERIOD_END}' && "
            f"python src/pipeline/dq.py --config {CONFIG} "
            f"--mart-path '{MART_PATH}'"
        ),
    )

    extract >> transform >> dq >> load
