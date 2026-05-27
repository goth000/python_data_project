import json
from datetime import datetime
from pathlib import Path

import requests
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "configs" / "variant_06.yml"
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def fetch_json(url: str, params: dict, timeout: int = 10) -> tuple[dict | None, int]:
    try:
        response = requests.get(url, params=params, timeout=timeout)
        status_code = response.status_code

        if not response.ok:
            print(f"[ERROR] HTTP error: status={status_code}")
            return None, status_code

        try:
            return response.json(), status_code
        except ValueError:
            print("[ERROR] Response is not valid JSON")
            return None, status_code

    except requests.exceptions.Timeout:
        print("[ERROR] Request timeout")
        return None, 0
    except requests.exceptions.RequestException as error:
        print(f"[ERROR] Request failed: {error}")
        return None, 0


def save_raw_json(data: dict, variant_id: str) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_name = f"variant_{variant_id}"

    output_dir = RAW_DIR / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{timestamp}.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    return output_path


def main() -> None:
    config = load_config(CONFIG_PATH)

    variant_id = str(config["variant_id"]).zfill(2)
    source_type = config["source_type"]

    api_config = config["api"]
    base_url = api_config["base_url"]
    method = api_config.get("method", "GET")
    params = api_config.get("params", {})
    timeout = api_config.get("timeout_sec", 10)

    params["start_date"] = "2024-05-01"
    params["end_date"] = "2024-05-07"

    if method.upper() != "GET":
        print(f"[ERROR] Unsupported method: {method}")
        return

    data, status_code = fetch_json(base_url, params=params, timeout=timeout)

    if data is None:
        print("[ERROR] No data saved")
        return

    output_path = save_raw_json(data, variant_id)

    print("[OK] Extract completed")
    print(f"variant: variant_{variant_id}")
    print(f"source: {source_type}")
    print(f"url: {base_url}")
    print(f"status: {status_code}")
    print(f"saved_to: {output_path}")
    print(f"top_level_keys: {list(data.keys())}")


if __name__ == "__main__":
    main()