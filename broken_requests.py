import argparse
import time

import requests


def run_broken_example() -> None:
    """Run the original unsafe request from the assignment."""
    url = "https://httpbin.org/delay/10"
    print("[BROKEN] No timeout, status check, exception handling, or JSON check")
    print(f"[BROKEN] Requesting: {url}")

    started_at = time.monotonic()

    # Intentionally broken: this code demonstrates why each safeguard is needed.
    response = requests.get(url)
    data = response.json()

    elapsed = time.monotonic() - started_at
    print(f"[BROKEN] Completed after approximately {elapsed:.1f} seconds")
    print("ok:", data["url"])


def check_url(url: str, timeout: int = 3) -> None:
    """Request a URL and report expected HTTP and response-format errors."""
    print(f"[INFO] Requesting: {url}")

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        try:
            data = response.json()
        except ValueError:
            print("[ERROR] Response is not JSON")
            return

        print("[OK] Request completed")
        print(data)
    except requests.exceptions.Timeout:
        print(f"[ERROR] Request timed out after {timeout} seconds")
    except requests.exceptions.HTTPError as error:
        print(f"[ERROR] HTTP status: {error.response.status_code}")
    except requests.exceptions.RequestException as error:
        print(f"[ERROR] Network error: {error}")


def run_fixed_examples() -> None:
    print("[FIXED] Requests use timeout and handle expected errors")
    check_url("https://httpbin.org/delay/10", timeout=3)
    check_url("https://httpbin.org/status/404", timeout=10)
    check_url("https://httpbin.org/html", timeout=10)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Demonstrate broken and fixed requests code."
    )
    parser.add_argument(
        "--broken",
        action="store_true",
        help="run the intentionally unsafe original example",
    )
    args = parser.parse_args()

    if args.broken:
        run_broken_example()
    else:
        run_fixed_examples()


if __name__ == "__main__":
    main()
