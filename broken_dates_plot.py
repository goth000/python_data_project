from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
FIGURES_DIR = PROJECT_ROOT / "docs" / "figures"


def save_plot(df: pd.DataFrame, title: str, output_name: str) -> None:
    plt.figure(figsize=(8, 5))
    plt.plot(df["date"], df["value"], marker="o")
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Value")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / output_name)
    plt.close()


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(
        {
            "date": ["2025-01-10", "2025-01-2", "2025-01-3"],
            "value": [10, 2, 3],
        }
    )

    broken_df = df.sort_values("date")
    print("[BROKEN] String order:", broken_df["date"].tolist())
    save_plot(
        broken_df,
        "Broken Time Series: Dates Sorted as Strings",
        "broken_dates_plot.png",
    )

    fixed_df = df.copy()
    fixed_df["date"] = pd.to_datetime(fixed_df["date"])
    fixed_df = fixed_df.sort_values("date")
    print(
        "[FIXED] Datetime order:",
        fixed_df["date"].dt.strftime("%Y-%m-%d").tolist(),
    )
    save_plot(
        fixed_df,
        "Fixed Time Series: Dates Sorted Chronologically",
        "fixed_dates_plot.png",
    )

    print(
        "[EXPLANATION] Strings are sorted character by character, so "
        "2025-01-10 appears before 2025-01-2. Datetime values are sorted "
        "in calendar order and do not create a false time-series jump."
    )
    print(f"[OK] Figures saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
