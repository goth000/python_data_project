import pendulum

from airflow import DAG
from airflow.operators.bash import BashOperator


PROJECT_DIR = "/opt/airflow/project"
CONFIG = "configs/variant_06.yml"
RAW_PATH = "data/raw/variant_06/airflow_{{ ts_nodash }}.json"
NORMALIZED_PATH = "data/normalized/variant_06/airflow_{{ ts_nodash }}.csv"
MART_PATH = "data/mart/variant_06/mart_daily_airflow_{{ ts_nodash }}.csv"


with DAG(
    dag_id="etl_variant_06",
    start_date=pendulum.datetime(2026, 3, 1, tz="UTC"),
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=["etl", "variant_06", "open_meteo"],
):

    extract = BashOperator(
        task_id="extract",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "echo '[INFO] Airflow ds={{ ds }}' && "
            f"python src/pipeline/extract.py --config {CONFIG} "
            f"--output-path '{RAW_PATH}'"
        ),
    )

    transform = BashOperator(
        task_id="transform",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "echo '[INFO] Airflow ds={{ ds }}' && "
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
            "echo '[INFO] Airflow ds={{ ds }}' && "
            "POSTGRES_HOST=postgres "
            "POSTGRES_PORT=5432 "
            "POSTGRES_DB=analytics "
            "POSTGRES_USER=student "
            "POSTGRES_PASSWORD=student_pw "
            f"python src/pipeline/load.py --config {CONFIG} "
            f"--mart-path '{MART_PATH}'"
        ),
    )

    dq = BashOperator(
        task_id="dq",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "echo '[INFO] Airflow ds={{ ds }}' && "
            f"python src/pipeline/dq.py --config {CONFIG} "
            f"--mart-path '{MART_PATH}'"
        ),
    )

    extract >> transform >> dq >> load
