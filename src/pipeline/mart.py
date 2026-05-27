from datetime import datetime
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

NORMALIZED_DIR = PROJECT_ROOT / "data" / "normalized" / "variant_06"
MART_DIR = PROJECT_ROOT / "data" / "mart" / "variant_06"
REFERENCE_PATH = PROJECT_ROOT / "reference" / "cities.csv"


def get_latest_normalized_file() -> Path:
    files = sorted(NORMALIZED_DIR.glob("*.csv"))

    if not files:
        raise FileNotFoundError("No normalized CSV files found")

    return files[-1]


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    normalized_path = get_latest_normalized_file()

    print("[INFO] normalized file:", normalized_path)

    df = pd.read_csv(normalized_path)
    cities = pd.read_csv(REFERENCE_PATH)

    return df, cities


def validate_reference(cities: pd.DataFrame) -> None:
    if "city_id" not in cities.columns:
        raise ValueError("cities.csv must contain city_id column")

    if cities["city_id"].isna().any():
        raise ValueError("cities.csv contains empty city_id values")

    if cities["city_id"].duplicated().any():
        duplicates = cities[cities["city_id"].duplicated(keep=False)]
        raise ValueError(f"Duplicate city_id values found:\n{duplicates}")

    print("[OK] Reference table is valid")


def join_city_reference(df: pd.DataFrame, cities: pd.DataFrame) -> pd.DataFrame:
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

    return merged


def build_daily_mart(df: pd.DataFrame) -> pd.DataFrame:
    df["ts"] = pd.to_datetime(df["ts"])
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

    return mart


def save_mart(mart: pd.DataFrame) -> Path:
    MART_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = MART_DIR / f"mart_daily_{timestamp}.csv"

    mart.to_csv(output_path, index=False, encoding="utf-8")

    return output_path


def main() -> None:
    df, cities = load_data()

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

    output_path = save_mart(mart)

    print("[OK] Mart saved:", output_path)


if __name__ == "__main__":
    main()