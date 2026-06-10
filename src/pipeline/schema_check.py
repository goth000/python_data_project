import argparse
import json
from pathlib import Path

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_data_path(config: dict, layer: str, path_argument: str | None) -> Path:
    if path_argument:
        return PROJECT_ROOT / path_argument

    variant_id = str(config["variant_id"]).zfill(2)
    if layer == "mart":
        state_path = PROJECT_ROOT / "data" / "state" / f"state_variant_{variant_id}.json"
        if state_path.exists():
            with open(state_path, "r", encoding="utf-8") as file:
                return PROJECT_ROOT / json.load(file)["last_mart_file"]
        pattern = "mart_daily_*.csv"
    else:
        pattern = "*.csv"

    data_dir = PROJECT_ROOT / "data" / layer / f"variant_{variant_id}"
    files = sorted(data_dir.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No {layer} files found in {data_dir}")
    return files[-1]


def dtype_matches(series: pd.Series, expected: str) -> bool:
    if expected == "string":
        return pd.api.types.is_string_dtype(series)
    if expected == "integer":
        return pd.api.types.is_integer_dtype(series)
    if expected == "float":
        return pd.api.types.is_float_dtype(series)
    if expected in {"date", "datetime"}:
        return pd.to_datetime(series, errors="coerce").notna().all()
    raise ValueError(f"Unsupported contract dtype: {expected}")


def check_schema(df: pd.DataFrame, contract: list[dict]) -> bool:
    expected_columns = [field["name"] for field in contract]
    actual_columns = list(df.columns)
    passed = True

    missing = [column for column in expected_columns if column not in actual_columns]
    extra = [column for column in actual_columns if column not in expected_columns]

    print("[INFO] expected columns:", expected_columns)
    print("[INFO] actual columns:", actual_columns)

    if missing:
        print("[FAIL] Missing columns:", missing)
        passed = False
    if extra:
        print("[WARNING] Extra columns:", extra)
    if actual_columns[: len(expected_columns)] != expected_columns:
        print("[FAIL] Contract columns are missing or in the wrong order")
        passed = False

    for field in contract:
        column = field["name"]
        if column not in df.columns:
            continue
        if not dtype_matches(df[column], field["dtype"]):
            print(
                f"[FAIL] {column}: expected dtype={field['dtype']}, "
                f"actual dtype={df[column].dtype}"
            )
            passed = False
        if not field["nullable"] and df[column].isna().any():
            print(f"[FAIL] {column}: NULL values are not allowed")
            passed = False

    print("[PASS] Schema matches Data Contract" if passed else "[FAIL] Schema mismatch")
    return passed


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a data layer against contract")
    parser.add_argument("--config", default="configs/variant_06.yml")
    parser.add_argument("--layer", choices=["normalized", "mart"], default="mart")
    parser.add_argument("--data-path")
    args = parser.parse_args()

    config = load_config(PROJECT_ROOT / args.config)
    data_path = get_data_path(config, args.layer, args.data_path)
    contract = config[f"{args.layer}_schema"]

    print(f"[INFO] layer: {args.layer}")
    print(f"[INFO] data: {data_path}")
    df = pd.read_csv(data_path)

    if not check_schema(df, contract):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
