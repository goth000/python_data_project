from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MART_DIR = PROJECT_ROOT / "data" / "mart" / "variant_06"


EXPECTED_COLUMNS = [
    "date",
    "city_id",
    "city_name",
    "country_code",
    "timezone",
    "t_mean",
    "t_max",
    "precipitation_sum",
    "rainy_hours",
    "wind_speed_max",
]


def get_latest_mart_file() -> Path:
    files = sorted(MART_DIR.glob("mart_daily_*.csv"))

    if not files:
        raise FileNotFoundError("No mart files found")

    return files[-1]


def check_schema(df: pd.DataFrame) -> bool:
    actual_columns = list(df.columns)

    missing_columns = [
        column for column in EXPECTED_COLUMNS
        if column not in actual_columns
    ]

    extra_columns = [
        column for column in actual_columns
        if column not in EXPECTED_COLUMNS
    ]

    print("[INFO] expected columns:")
    print(EXPECTED_COLUMNS)

    print("\n[INFO] actual columns:")
    print(actual_columns)

    if missing_columns:
        print("\n[FAIL] Missing columns:")
        print(missing_columns)

    if extra_columns:
        print("\n[FAIL] Extra columns:")
        print(extra_columns)

    if actual_columns != EXPECTED_COLUMNS:
        print("\n[FAIL] Column order or schema does not match contract")
        return False

    print("\n[PASS] Schema matches Data Contract")
    return True


def main() -> None:
    mart_path = get_latest_mart_file()

    print("[INFO] latest mart:", mart_path)

    df = pd.read_csv(mart_path)

    is_valid = check_schema(df)

    if not is_valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()