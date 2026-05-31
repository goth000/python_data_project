from pathlib import Path
import os

import pandas as pd
from sqlalchemy import create_engine


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MART_DIR = PROJECT_ROOT / "data" / "mart" / "variant_06"


DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "analytics"),
    "user": os.getenv("POSTGRES_USER", "student"),
    "password": os.getenv("POSTGRES_PASSWORD", "student_pw"),
}


TABLE_NAME = "mart_open_meteo"


def get_latest_mart_file() -> Path:
    files = sorted(MART_DIR.glob("*.csv"))

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


def main() -> None:
    mart_path = get_latest_mart_file()

    print("[INFO] mart file:", mart_path)

    df = pd.read_csv(mart_path)

    print("[INFO] shape:", df.shape)
    print("[INFO] columns:", list(df.columns))
    print("[INFO] dtypes:")
    print(df.dtypes)

    connection_string = build_connection_string()

    engine = create_engine(connection_string)

    print("[INFO] connecting to postgres...")

    with engine.begin() as conn:
        df.to_sql(
            TABLE_NAME,
            conn,
            if_exists="replace",
            index=False,
        )

    print("[OK] data loaded to postgres")
    print("[OK] table:", TABLE_NAME)
    print("[OK] rows loaded:", len(df))


if __name__ == "__main__":
    main()