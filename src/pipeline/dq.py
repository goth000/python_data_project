import argparse
import json
from pathlib import Path

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "docs" / "dq_report.json"


def load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_mart_path(config: dict, mart_argument: str | None = None) -> Path:
    if mart_argument:
        return PROJECT_ROOT / mart_argument

    variant_id = str(config["variant_id"]).zfill(2)
    state_path = PROJECT_ROOT / "data" / "state" / f"state_variant_{variant_id}.json"
    if state_path.exists():
        with open(state_path, "r", encoding="utf-8") as file:
            state = json.load(file)
        return PROJECT_ROOT / state["last_mart_file"]

    mart_dir = PROJECT_ROOT / "data" / "mart" / f"variant_{variant_id}"
    mart_files = sorted(mart_dir.glob("mart_daily_*.csv"))
    if not mart_files:
        raise FileNotFoundError(f"No mart files found in {mart_dir}")
    return mart_files[-1]


def make_result(
    check_name: str,
    passed: bool,
    details: str,
    severity: str = "critical",
) -> dict:
    status = "PASS" if passed else ("WARNING" if severity == "warning" else "FAIL")
    return {
        "check": check_name,
        "status": status,
        "severity": severity,
        "details": details,
    }


def check_non_empty(
    df: pd.DataFrame,
    check_name: str = "non_empty",
    severity: str = "critical",
) -> dict:
    return make_result(
        check_name,
        not df.empty,
        f"rows={len(df)}" if not df.empty else "table is empty",
        severity,
    )


def check_not_null(
    df: pd.DataFrame,
    column: str,
    check_name: str | None = None,
    severity: str = "critical",
) -> dict:
    null_count = int(df[column].isna().sum())
    return make_result(
        check_name or f"not_null_{column}",
        null_count == 0,
        "no nulls" if null_count == 0 else f"null_count={null_count}",
        severity,
    )


def check_unique_business_key(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    check_name: str = "unique_business_key",
    severity: str = "critical",
) -> dict:
    key_columns = columns or ["date", "city_id"]
    duplicates = int(df.duplicated(subset=key_columns).sum())
    return make_result(
        check_name,
        duplicates == 0,
        "no duplicates" if duplicates == 0 else f"duplicates={duplicates}",
        severity,
    )


def check_numeric_range(
    df: pd.DataFrame,
    column: str,
    minimum: float | None = None,
    maximum: float | None = None,
    check_name: str | None = None,
    severity: str = "critical",
) -> dict:
    values = pd.to_numeric(df[column], errors="coerce")
    invalid = values.isna()
    if minimum is not None:
        invalid |= values < minimum
    if maximum is not None:
        invalid |= values > maximum
    invalid_count = int(invalid.sum())
    limits = f"min={minimum}, max={maximum}"
    details = (
        f"all values valid ({limits})"
        if invalid_count == 0
        else f"invalid_rows={invalid_count} ({limits})"
    )
    return make_result(
        check_name or f"{column}_range",
        invalid_count == 0,
        details,
        severity,
    )


def check_temperature_range(
    df: pd.DataFrame,
    minimum: float = -80,
    maximum: float = 60,
    severity: str = "warning",
) -> dict:
    return check_numeric_range(
        df, "t_mean", minimum, maximum, "temperature_range", severity
    )


def check_non_negative_precipitation(
    df: pd.DataFrame,
    severity: str = "critical",
) -> dict:
    return check_numeric_range(
        df,
        "precipitation_sum",
        minimum=0,
        check_name="non_negative_precipitation",
        severity=severity,
    )


def check_non_negative_wind(
    df: pd.DataFrame,
    severity: str = "warning",
) -> dict:
    return check_numeric_range(
        df,
        "wind_speed_max",
        minimum=0,
        check_name="non_negative_wind",
        severity=severity,
    )


def run_rule(df: pd.DataFrame, rule: dict) -> dict:
    rule_type = rule["type"]
    name = rule["name"]
    severity = rule.get("severity", "critical")

    if rule_type == "non_empty":
        return check_non_empty(df, name, severity)
    if rule_type == "not_null":
        return check_not_null(df, rule["column"], name, severity)
    if rule_type == "unique":
        return check_unique_business_key(df, rule["columns"], name, severity)
    if rule_type == "numeric_range":
        return check_numeric_range(
            df,
            rule["column"],
            rule.get("min"),
            rule.get("max"),
            name,
            severity,
        )
    raise ValueError(f"Unsupported DQ rule type: {rule_type}")


def save_report(results: list[dict], mart_path: Path) -> None:
    try:
        dataset_path = mart_path.relative_to(PROJECT_ROOT)
    except ValueError:
        dataset_path = mart_path

    report = {
        "dataset": str(dataset_path),
        "summary": {
            status: sum(result["status"] == status for result in results)
            for status in ["PASS", "WARNING", "FAIL"]
        },
        "checks": results,
    }
    with open(REPORT_PATH, "w", encoding="utf-8", newline="\n") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
    print(f"[OK] dq report saved: {REPORT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run configured data quality checks")
    parser.add_argument("--config", default="configs/variant_06.yml")
    parser.add_argument("--mart-path")
    args = parser.parse_args()

    config = load_config(PROJECT_ROOT / args.config)
    mart_path = get_mart_path(config, args.mart_path)
    print(f"[INFO] mart: {mart_path}")
    df = pd.read_csv(mart_path)
    print(f"[INFO] shape: {df.shape}")

    results = [run_rule(df, rule) for rule in config["dq_rules"]]
    print("\n=== DQ REPORT ===")
    for result in results:
        print(result)
    save_report(results, mart_path)

    if any(result["status"] == "FAIL" for result in results):
        raise SystemExit("[ERROR] Critical DQ checks failed")


if __name__ == "__main__":
    main()
