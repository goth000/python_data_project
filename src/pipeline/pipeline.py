import argparse
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = PROJECT_ROOT / "data" / "state"


def run_step(command: list[str], step_name: str) -> None:
    print(f"\n[INFO] Starting step: {step_name}")

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )

    print(result.stdout)

    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(f"Step failed: {step_name}")

    print(f"[OK] Step completed: {step_name}")


def load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_state_path(variant_id: str) -> Path:
    return STATE_DIR / f"state_variant_{variant_id}.json"


def load_state(variant_id: str) -> dict:
    state_path = get_state_path(variant_id)

    if not state_path.exists():
        raise FileNotFoundError(
            f"State file not found: {state_path}. Run the pipeline in full mode first."
        )

    with open(state_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_latest_file(directory: Path, pattern: str) -> Path:
    files = sorted(directory.glob(pattern))

    if not files:
        raise FileNotFoundError(f"No files matching {pattern} found in {directory}")

    return files[-1]


def get_watermark_from_mart(mart_path: Path) -> str:
    df = pd.read_csv(mart_path)
    return str(pd.to_datetime(df["date"]).max().date())


def save_state(config: dict, mode: str, watermark: str, mart_path: Path) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    variant_id = str(config["variant_id"]).zfill(2)
    state_path = get_state_path(variant_id)
    temporary_path = state_path.with_suffix(".json.tmp")

    state = {
        "variant_id": variant_id,
        "source_type": config["source_type"],
        "mode": mode,
        "last_watermark": watermark,
        "business_key": ["date", "city_id"],
        "last_mart_file": mart_path.relative_to(PROJECT_ROOT).as_posix(),
        "last_successful_run": datetime.now().isoformat(timespec="seconds"),
    }

    with open(temporary_path, "w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)

    temporary_path.replace(state_path)

    return state_path


def parse_date(value: str | date, field_name: str) -> date:
    if isinstance(value, date):
        return value

    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid {field_name}: {value}") from error


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ETL pipeline")
    parser.add_argument("--config", required=True)
    parser.add_argument("--mode", choices=["full", "incremental"], required=True)

    args = parser.parse_args()

    config_path = PROJECT_ROOT / args.config
    config = load_config(config_path)
    variant_id = str(config["variant_id"]).zfill(2)
    raw_dir = PROJECT_ROOT / "data" / "raw" / f"variant_{variant_id}"
    normalized_dir = PROJECT_ROOT / "data" / "normalized" / f"variant_{variant_id}"
    mart_dir = PROJECT_ROOT / "data" / "mart" / f"variant_{variant_id}"
    configured_start = parse_date(config["api"]["params"]["start_date"], "start_date")
    configured_end = parse_date(config["api"]["params"]["end_date"], "end_date")
    if configured_start > configured_end:
        raise ValueError("Configured start_date must not be after end_date")

    print("[INFO] ETL pipeline started")
    print(f"[INFO] config: {config_path}")
    print(f"[INFO] mode: {args.mode}")

    if args.mode == "full":
        print("[INFO] Full mode: rebuild all layers and replace PostgreSQL table")
        start_date = configured_start
    else:
        state = load_state(variant_id)
        watermark = parse_date(state["last_watermark"], "last_watermark")
        start_date = watermark + timedelta(days=1)
        print(f"[INFO] Current watermark: {watermark}")

        if start_date > configured_end:
            latest_mart = get_latest_file(mart_dir, "mart_daily_*.csv")
            state_path = save_state(
                config=config,
                mode=args.mode,
                watermark=str(watermark),
                mart_path=latest_mart,
            )
            print("[OK] No new dates to process")
            print(f"[OK] configured end date: {configured_end}")
            print(f"[OK] state saved: {state_path}")
            return

        print(f"[INFO] Incremental period: {start_date} -> {configured_end}")

    python_executable = sys.executable
    config_argument = str(config_path.relative_to(PROJECT_ROOT))

    run_step(
        [
            python_executable,
            "src/pipeline/extract.py",
            "--config",
            config_argument,
            "--start-date",
            str(start_date),
            "--end-date",
            str(configured_end),
        ],
        "extract",
    )
    latest_raw = get_latest_file(raw_dir, "*.json")

    run_step(
        [
            python_executable,
            "src/pipeline/normalize.py",
            "--config",
            config_argument,
            "--raw-path",
            str(latest_raw.relative_to(PROJECT_ROOT)),
        ],
        "normalize",
    )
    latest_normalized = get_latest_file(normalized_dir, "*.csv")

    run_step(
        [
            python_executable,
            "src/pipeline/mart.py",
            "--config",
            config_argument,
            "--normalized-path",
            str(latest_normalized.relative_to(PROJECT_ROOT)),
        ],
        "mart",
    )
    latest_mart = get_latest_file(mart_dir, "mart_daily_*.csv")

    run_step(
        [
            python_executable,
            "src/pipeline/dq.py",
            "--config",
            config_argument,
            "--mart-path",
            str(latest_mart.relative_to(PROJECT_ROOT)),
        ],
        "data quality",
    )

    run_step(
        [
            python_executable,
            "src/pipeline/load.py",
            "--config",
            config_argument,
            "--mart-path",
            str(latest_mart.relative_to(PROJECT_ROOT)),
            "--mode",
            args.mode,
        ],
        "load",
    )

    watermark = get_watermark_from_mart(latest_mart)

    state_path = save_state(
        config=config,
        mode=args.mode,
        watermark=watermark,
        mart_path=latest_mart,
    )

    print("\n[OK] ETL pipeline completed")
    print(f"[OK] latest_mart: {latest_mart}")
    print(f"[OK] watermark: {watermark}")
    print(f"[OK] state saved: {state_path}")


if __name__ == "__main__":
    main()
