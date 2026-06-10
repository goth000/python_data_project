import requests


def check_url(url: str, timeout: int = 3) -> None:
    print(f"[INFO] Requesting: {url}")

    try:
        response = requests.get(url, timeout=timeout)

        if not response.ok:
            print(f"[ERROR] HTTP status: {response.status_code}")
            return

        try:
            data = response.json()
        except ValueError:
            print("[ERROR] Response is not JSON")
            return

        print("[OK] Request completed")
        print(data)

    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out")
    except requests.exceptions.RequestException as error:
        print(f"[ERROR] Network error: {error}")


def main() -> None:
    check_url("https://httpbin.org/delay/10", timeout=3)
    check_url("https://httpbin.org/status/404", timeout=3)
    check_url("https://httpbin.org/html", timeout=3)


if __name__ == "__main__":
    main()
