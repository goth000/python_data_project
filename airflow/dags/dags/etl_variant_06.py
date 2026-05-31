import pendulum

from airflow import DAG
from airflow.operators.bash import BashOperator


PROJECT_DIR = "/opt/airflow/project"


with DAG(
    dag_id="etl_variant_06",
    start_date=pendulum.datetime(2026, 3, 1, tz="UTC"),
    schedule="*/5 * * * *",
    catchup=False,
    tags=["etl", "variant_06", "open_meteo"],
):

    extract = BashOperator(
        task_id="extract",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "echo '[INFO] Airflow ds={{ ds }}' && "
            "python src/pipeline/extract.py"
        ),
    )

    transform = BashOperator(
        task_id="transform",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "echo '[INFO] Airflow ds={{ ds }}' && "
            "python src/pipeline/normalize.py && "
            "python src/pipeline/mart.py"
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
            "python src/pipeline/load.py"
        ),
    )

    dq = BashOperator(
        task_id="dq",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "echo '[INFO] Airflow ds={{ ds }}' && "
            "python src/pipeline/dq.py"
        ),
    )

    extract >> transform >> dq >> load