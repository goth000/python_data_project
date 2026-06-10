import argparse
from pathlib import Path
import os

import pandas as pd
from sqlalchemy import create_engine, inspect, text
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "analytics"),
    "user": os.getenv("POSTGRES_USER", "student"),
    "password": os.getenv("POSTGRES_PASSWORD", "student_pw"),
}


TABLE_NAME = "mart_open_meteo"
UNIQUE_INDEX_NAME = "mart_open_meteo_date_city_id_uidx"


def load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_latest_mart_file(variant_id: str) -> Path:
    mart_dir = PROJECT_ROOT / "data" / "mart" / f"variant_{variant_id}"
    files = sorted(mart_dir.glob("*.csv"))

    if not files:
        raise FileNotFoundError("No mart files found")

    return files[-1]


def build_connection_string() -> str:
    return (
        f"postgresql+psycopg2://"
        f"{DB_CONFIG['user']}:"
        f"{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:"
        f"{DB_CONFIG['port']}/"
        f"{DB_CONFIG['database']}"
    )


def load_dataframe(conn, df: pd.DataFrame, mode: str) -> int:
    duplicate_count = int(df.duplicated(subset=["date", "city_id"]).sum())
    if duplicate_count:
        raise ValueError(f"MART contains duplicate business keys: {duplicate_count}")

    table_exists = inspect(conn).has_table(TABLE_NAME)
    deleted_rows = 0
    if mode == "incremental" and table_exists:
        for city_id in df["city_id"].drop_duplicates():
            result = conn.execute(
                text(
                    f'DELETE FROM "{TABLE_NAME}" '
                    "WHERE city_id = :city_id AND date BETWEEN :start_date AND :end_date"
                ),
                {
                    "city_id": city_id,
                    "start_date": df["date"].min(),
                    "end_date": df["date"].max(),
                },
            )
            deleted_rows += max(result.rowcount, 0)
        if_exists = "append"
    else:
        if_exists = "replace"

    df.to_sql(TABLE_NAME, conn, if_exists=if_exists, index=False)
    conn.execute(
        text(
            f'CREATE UNIQUE INDEX IF NOT EXISTS "{UNIQUE_INDEX_NAME}" '
            f'ON "{TABLE_NAME}" (date, city_id)'
        )
    )
    return deleted_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Load MART data into PostgreSQL")
    parser.add_argument("--config", default="configs/variant_06.yml")
    parser.add_argument("--mart-path")
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    args = parser.parse_args()

    config = load_config(PROJECT_ROOT / args.config)
    variant_id = str(config["variant_id"]).zfill(2)
    mart_path = (
        PROJECT_ROOT / args.mart_path
        if args.mart_path
        else get_latest_mart_file(variant_id)
    )

    print("[INFO] mart file:", mart_path)

    df = pd.read_csv(mart_path)
    df["date"] = pd.to_datetime(df["date"], errors="raise").dt.date

    print("[INFO] shape:", df.shape)
    print(f"[INFO] load period: {df['date'].min()} -> {df['date'].max()}")
    print("[INFO] columns:", list(df.columns))
    print("[INFO] dtypes:")
    print(df.dtypes)

    connection_string = build_connection_string()

    engine = create_engine(connection_string)

    print("[INFO] connecting to postgres...")

    with engine.begin() as conn:
        deleted_rows = load_dataframe(conn, df, args.mode)

    print("[OK] data loaded to postgres")
    print("[OK] table:", TABLE_NAME)
    print("[OK] rows loaded:", len(df))
    print("[OK] rows deleted before insert:", deleted_rows)
    print("[OK] load mode:", args.mode)


if __name__ == "__main__":
    main()
