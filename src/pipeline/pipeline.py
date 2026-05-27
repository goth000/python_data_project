import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = PROJECT_ROOT / "data" / "state"
MART_DIR = PROJECT_ROOT / "data" / "mart" / "variant_06"


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


def get_latest_mart_file() -> Path:
    files = sorted(MART_DIR.glob("mart_daily_*.csv"))

    if not files:
        raise FileNotFoundError("No mart files found")

    return files[-1]


def get_watermark_from_mart(mart_path: Path) -> str:
    df = pd.read_csv(mart_path)
    return str(pd.to_datetime(df["date"]).max().date())


def save_state(config: dict, mode: str, watermark: str, mart_path: Path) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    variant_id = str(config["variant_id"]).zfill(2)
    state_path = STATE_DIR / f"state_variant_{variant_id}.json"

    state = {
        "variant_id": variant_id,
        "source_type": config["source_type"],
        "mode": mode,
        "last_watermark": watermark,
        "business_key": ["date", "city_id"],
        "last_mart_file": str(mart_path),
        "last_successful_run": datetime.now().isoformat(timespec="seconds"),
    }

    with open(state_path, "w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)

    return state_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ETL pipeline")
    parser.add_argument("--config", required=True)
    parser.add_argument("--mode", choices=["full", "incremental"], required=True)

    args = parser.parse_args()

    config_path = PROJECT_ROOT / args.config
    config = load_config(config_path)

    print("[INFO] ETL pipeline started")
    print(f"[INFO] config: {config_path}")
    print(f"[INFO] mode: {args.mode}")

    if args.mode == "full":
        print("[INFO] Full mode: rebuild all layers and replace PostgreSQL table")
    else:
        print("[INFO] Incremental mode: run pipeline and update watermark safely")

    python_executable = sys.executable

    run_step(
        [python_executable, "src/pipeline/extract.py"],
        "extract",
    )

    run_step(
        [python_executable, "src/pipeline/normalize.py"],
        "normalize",
    )

    run_step(
        [python_executable, "src/pipeline/mart.py"],
        "mart",
    )

    run_step(
        [python_executable, "src/pipeline/load.py"],
        "load",
    )

    latest_mart = get_latest_mart_file()
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