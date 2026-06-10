import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = PROJECT_ROOT / "reference" / "cities.csv"
REFERENCE_COLUMNS = [
    "city_id",
    "city_name",
    "country_code",
    "timezone",
]
NORMALIZED_COLUMNS = [
    "ts",
    "city_id",
    "temperature_2m",
    "precipitation",
    "wind_speed_10m",
]


def load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_latest_normalized_file(variant_id: str) -> Path:
    normalized_dir = PROJECT_ROOT / "data" / "normalized" / f"variant_{variant_id}"
    files = sorted(normalized_dir.glob("*.csv"))

    if not files:
        raise FileNotFoundError("No normalized CSV files found")

    return files[-1]


def load_data(normalized_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:

    print("[INFO] normalized file:", normalized_path)

    df = pd.read_csv(normalized_path)
    cities = pd.read_csv(REFERENCE_PATH)

    return df, cities


def validate_reference(cities: pd.DataFrame) -> None:
    missing_columns = [
        column for column in REFERENCE_COLUMNS if column not in cities.columns
    ]
    if missing_columns:
        raise ValueError(f"cities.csv is missing required columns: {missing_columns}")

    null_counts = cities[REFERENCE_COLUMNS].isna().sum()
    columns_with_nulls = null_counts[null_counts > 0].to_dict()
    if columns_with_nulls:
        raise ValueError(
            f"cities.csv contains empty required values: {columns_with_nulls}"
        )

    if cities["city_id"].duplicated().any():
        duplicates = cities[cities["city_id"].duplicated(keep=False)]
        raise ValueError(f"Duplicate city_id values found:\n{duplicates}")

    print("[OK] Reference table is valid")


def join_city_reference(df: pd.DataFrame, cities: pd.DataFrame) -> pd.DataFrame:
    missing_columns = [
        column for column in NORMALIZED_COLUMNS if column not in df.columns
    ]
    if missing_columns:
        raise ValueError(f"Normalized data is missing required columns: {missing_columns}")

    rows_before = len(df)

    merged = df.merge(
        cities,
        on="city_id",
        how="left",
        validate="many_to_one"
    )

    rows_after = len(merged)

    print("[INFO] rows before merge:", rows_before)
    print("[INFO] rows after merge:", rows_after)

    if rows_before != rows_after:
        raise ValueError("Rows count changed after merge")

    missing_reference = merged[REFERENCE_COLUMNS[1:]].isna().any(axis=1)
    if missing_reference.any():
        missing_ids = (
            merged.loc[missing_reference, "city_id"].drop_duplicates().tolist()
        )
        raise ValueError(f"Missing reference data for city_id: {missing_ids}")

    return merged


def build_daily_mart(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ts"] = pd.to_datetime(df["ts"], errors="coerce")

    if df["ts"].isna().any():
        raise ValueError("Normalized data contains invalid timestamps")

    df["date"] = df["ts"].dt.date

    mart = (
        df.groupby(["date", "city_id", "city_name", "country_code", "timezone"])
        .agg(
            t_mean=("temperature_2m", "mean"),
            t_max=("temperature_2m", "max"),
            precipitation_sum=("precipitation", "sum"),
            rainy_hours=("precipitation", lambda x: (x > 0).sum()),
            wind_speed_max=("wind_speed_10m", "max"),
        )
        .reset_index()
    )

    if mart.empty:
        raise ValueError("Daily MART is empty")

    return mart


def save_mart(
    mart: pd.DataFrame,
    variant_id: str,
    output_path: Path | None = None,
) -> Path:
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mart.to_csv(output_path, index=False, encoding="utf-8")
        return output_path

    mart_dir = PROJECT_ROOT / "data" / "mart" / f"variant_{variant_id}"
    mart_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    output_path = mart_dir / f"mart_daily_{timestamp}.csv"

    mart.to_csv(output_path, index=False, encoding="utf-8")

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the daily MART")
    parser.add_argument("--config", default="configs/variant_06.yml")
    parser.add_argument("--normalized-path")
    parser.add_argument("--output-path")
    args = parser.parse_args()

    config = load_config(PROJECT_ROOT / args.config)
    variant_id = str(config["variant_id"]).zfill(2)
    normalized_path = (
        PROJECT_ROOT / args.normalized_path
        if args.normalized_path
        else get_latest_normalized_file(variant_id)
    )

    df, cities = load_data(normalized_path)

    print("[INFO] normalized rows:", len(df))
    print("[INFO] normalized columns:", list(df.columns))
    print("[INFO] reference rows:", len(cities))
    print("[INFO] reference columns:", list(cities.columns))

    validate_reference(cities)

    merged = join_city_reference(df, cities)

    print("[INFO] merged head:")
    print(merged.head())

    mart = build_daily_mart(merged)

    print("[INFO] mart head:")
    print(mart.head())
    print("[INFO] mart shape:", mart.shape)

    output_path = save_mart(
        mart,
        variant_id,
        PROJECT_ROOT / args.output_path if args.output_path else None,
    )

    print("[OK] Mart saved:", output_path)


if __name__ == "__main__":
    main()
