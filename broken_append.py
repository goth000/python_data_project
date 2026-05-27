from pathlib import Path

import pandas as pd


OUTPUT_PATH = Path("out.csv")


def safe_replace() -> None:
    df = pd.DataFrame({
        "id": [1, 2],
        "v": [10, 20],
    })

    # SAFE: replace previous file instead of append
    df.to_csv(
        OUTPUT_PATH,
        mode="w",
        header=True,
        index=False,
    )

    print("[OK] File was rewritten safely")


def main() -> None:
    print("=== SAFE IDEMPOTENT VERSION ===")

    safe_replace()

    print("\nThis version is idempotent.")
    print("Running the script multiple times does not create duplicates.")
    print("The output file is fully replaced on every run.")


if __name__ == "__main__":
    main()