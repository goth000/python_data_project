import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "configs" / "variant_06.yml"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
NORMALIZED_DIR = PROJECT_ROOT / "data" / "normalized"

HOURLY_COLUMN_MAP = {
    "time": "ts",
    "temperature_2m": "temperature_2m",
    "relative_humidity_2m": "relative_humidity_2m",
    "precipitation": "precipitation",
    "wind_speed_10m": "wind_speed_10m",
}
NUMERIC_COLUMNS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
]
BUSINESS_KEY = ["city_id", "ts"]


def load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_latest_raw_file(variant_id: str) -> Path:
    raw_variant_dir = RAW_DIR / f"variant_{variant_id}"
    raw_files = sorted(raw_variant_dir.glob("*.json"))

    if not raw_files:
        raise FileNotFoundError(f"No RAW JSON files found in {raw_variant_dir}")

    return raw_files[-1]


def load_raw_json(raw_path: Path) -> dict:
    with open(raw_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("RAW JSON must contain an object at the top level")

    return data


def validate_hourly_data(data: dict) -> dict:
    hourly = data.get("hourly")

    if not isinstance(hourly, dict):
        raise ValueError("RAW JSON must contain an 'hourly' object")

    missing_columns = [
        column for column in HOURLY_COLUMN_MAP if column not in hourly
    ]
    if missing_columns:
        raise ValueError(f"Missing hourly columns: {missing_columns}")

    invalid_types = [
        column
        for column in HOURLY_COLUMN_MAP
        if not isinstance(hourly[column], list)
    ]
    if invalid_types:
        raise ValueError(f"Hourly columns must contain arrays: {invalid_types}")

    lengths = {column: len(hourly[column]) for column in HOURLY_COLUMN_MAP}
    if len(set(lengths.values())) != 1:
        raise ValueError(f"Hourly columns have different lengths: {lengths}")

    if not lengths["time"]:
        raise ValueError("Hourly data is empty")

    return hourly


def build_normalized_dataframe(hourly: dict, city_id: str) -> tuple[pd.DataFrame, int]:
    df = pd.DataFrame(
        {
            normalized_name: hourly[raw_name]
            for raw_name, normalized_name in HOURLY_COLUMN_MAP.items()
        }
    )
    df["city_id"] = city_id

    df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    null_counts = df.isna().sum()
    invalid_columns = null_counts[null_counts > 0].to_dict()
    if invalid_columns:
        raise ValueError(
            f"Missing or invalid values after type conversion: {invalid_columns}"
        )

    duplicate_count = int(df.duplicated(subset=BUSINESS_KEY).sum())
    df = df.drop_duplicates(subset=BUSINESS_KEY, keep="last")
    df = df.sort_values(BUSINESS_KEY).reset_index(drop=True)

    return df, duplicate_count


def save_normalized_csv(df: pd.DataFrame, variant_id: str) -> Path:
    output_dir = NORMALIZED_DIR / f"variant_{variant_id}"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    output_path = output_dir / f"{timestamp}.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")

    return output_path


def main() -> None:
    config = load_config(CONFIG_PATH)
    variant_id = str(config["variant_id"]).zfill(2)
    city_id = config["entity"]["city_id"]

    raw_path = get_latest_raw_file(variant_id)
    print(f"[INFO] RAW file: {raw_path}")

    data = load_raw_json(raw_path)
    hourly = validate_hourly_data(data)
    df, duplicate_count = build_normalized_dataframe(hourly, city_id)
    output_path = save_normalized_csv(df, variant_id)

    print(f"[INFO] Input rows: {len(hourly['time'])}")
    print(f"[INFO] Removed duplicate business keys: {duplicate_count}")
    print(f"[INFO] Output rows: {len(df)}")
    print(f"[INFO] Columns: {list(df.columns)}")
    print(f"[INFO] Time range: {df['ts'].min()} -> {df['ts'].max()}")
    print(f"[OK] Normalized CSV saved: {output_path}")


if __name__ == "__main__":
    main()
