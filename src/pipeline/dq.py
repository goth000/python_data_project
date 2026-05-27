from pathlib import Path
import json

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_latest_mart() -> pd.DataFrame:
    mart_dir = PROJECT_ROOT / "data" / "mart" / "variant_06"

    mart_files = sorted(mart_dir.glob("mart_daily_*.csv"))

    if not mart_files:
        raise FileNotFoundError("No mart files found")

    latest_mart = mart_files[-1]

    print(f"[INFO] latest mart: {latest_mart}")

    df = pd.read_csv(latest_mart)

    print(f"[INFO] shape: {df.shape}")

    return df


def make_result(
    check_name: str,
    status: str,
    details: str,
) -> dict:
    return {
        "check": check_name,
        "status": status,
        "details": details,
    }


def check_non_empty(df: pd.DataFrame) -> dict:
    if len(df) > 0:
        return make_result(
            "non_empty",
            "PASS",
            f"rows={len(df)}",
        )

    return make_result(
        "non_empty",
        "FAIL",
        "table is empty",
    )


def check_not_null(
    df: pd.DataFrame,
    column: str,
) -> dict:
    null_count = df[column].isna().sum()

    if null_count == 0:
        return make_result(
            f"not_null_{column}",
            "PASS",
            "no nulls",
        )

    return make_result(
        f"not_null_{column}",
        "FAIL",
        f"null_count={null_count}",
    )


def check_unique_business_key(
    df: pd.DataFrame,
) -> dict:
    duplicates = df.duplicated(
        subset=["date", "city_id"]
    ).sum()

    if duplicates == 0:
        return make_result(
            "unique_business_key",
            "PASS",
            "no duplicates",
        )

    return make_result(
        "unique_business_key",
        "FAIL",
        f"duplicates={duplicates}",
    )


def check_temperature_range(
    df: pd.DataFrame,
) -> dict:
    invalid = (
        (df["t_mean"] < -100)
        | (df["t_mean"] > 100)
    ).sum()

    if invalid == 0:
        return make_result(
            "temperature_range",
            "PASS",
            "all values valid",
        )

    return make_result(
        "temperature_range",
        "FAIL",
        f"invalid_rows={invalid}",
    )


def check_non_negative_precipitation(
    df: pd.DataFrame,
) -> dict:
    invalid = (
        df["precipitation_sum"] < 0
    ).sum()

    if invalid == 0:
        return make_result(
            "non_negative_precipitation",
            "PASS",
            "all values valid",
        )

    return make_result(
        "non_negative_precipitation",
        "FAIL",
        f"invalid_rows={invalid}",
    )


def check_non_negative_wind(
    df: pd.DataFrame,
) -> dict:
    invalid = (
        df["wind_speed_max"] < 0
    ).sum()

    if invalid == 0:
        return make_result(
            "non_negative_wind",
            "PASS",
            "all values valid",
        )

    return make_result(
        "non_negative_wind",
        "FAIL",
        f"invalid_rows={invalid}",
    )


def save_report(results: list[dict]) -> None:
    output_path = PROJECT_ROOT / "docs" / "dq_report.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"[OK] dq report saved: {output_path}")


def main() -> None:
    df = load_latest_mart()

    results = [
        check_non_empty(df),
        check_not_null(df, "date"),
        check_not_null(df, "city_id"),
        check_unique_business_key(df),
        check_temperature_range(df),
        check_non_negative_precipitation(df),
        check_non_negative_wind(df),
    ]

    print("\n=== DQ REPORT ===")

    for result in results:
        print(result)

    save_report(results)


if __name__ == "__main__":
    main()