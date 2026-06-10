from pathlib import Path
import tempfile

import pandas as pd


OUTPUT_PATH = Path(tempfile.gettempdir()) / "broken_append_example.csv"


def get_example_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": [1, 2],
            "value": [10, 20],
        }
    )


def broken_append() -> None:
    df = get_example_data()
    df.to_csv(
        OUTPUT_PATH,
        mode="a",
        header=not OUTPUT_PATH.exists(),
        index=False,
    )


def safe_replace() -> None:
    df = get_example_data()
    df.to_csv(
        OUTPUT_PATH,
        mode="w",
        header=True,
        index=False,
    )


def count_rows() -> int:
    return len(pd.read_csv(OUTPUT_PATH))


def main() -> None:
    OUTPUT_PATH.unlink(missing_ok=True)

    print("[INFO] Output file:", OUTPUT_PATH)

    broken_append()
    broken_append()
    print("[BROKEN] Rows after two append runs:", count_rows())
    print("[BROKEN] The same input was written twice, so duplicates appeared.")

    safe_replace()
    safe_replace()
    print("[FIXED] Rows after two replace runs:", count_rows())
    print("[FIXED] Replacing the file makes repeated runs idempotent.")


if __name__ == "__main__":
    main()
