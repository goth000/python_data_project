from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = (
    PROJECT_ROOT / "data" / "normalized" / "variant_06" / "2026-05-27_17-31-03.csv"
)
OUTPUT_DIR = PROJECT_ROOT / "docs" / "ml"
FEATURES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "hour_sin",
    "hour_cos",
]
TARGET = "target_temperature_next_hour"


def build_model_dataset(input_path: Path = INPUT_PATH) -> pd.DataFrame:
    df = pd.read_csv(input_path, parse_dates=["ts"]).sort_values("ts").reset_index(drop=True)
    df["hour_sin"] = np.sin(2 * np.pi * df["ts"].dt.hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["ts"].dt.hour / 24)
    df["target_ts"] = df["ts"].shift(-1)
    df[TARGET] = df["temperature_2m"].shift(-1)
    df = df.dropna(subset=["target_ts", TARGET])
    df = df[df["target_ts"] - df["ts"] == pd.Timedelta(hours=1)]
    return df.reset_index(drop=True)


def split_by_time(df: pd.DataFrame, train_fraction: float = 0.8):
    split_index = int(len(df) * train_fraction)
    if split_index <= 0 or split_index >= len(df):
        raise ValueError("Time split must create non-empty train and test sets")
    return df.iloc[:split_index].copy(), df.iloc[split_index:].copy()


def regression_metrics(actual, predicted) -> dict[str, float]:
    return {
        "MAE": mean_absolute_error(actual, predicted),
        "RMSE": mean_squared_error(actual, predicted) ** 0.5,
        "R2": r2_score(actual, predicted),
    }


def save_artifacts(
    train: pd.DataFrame,
    test: pd.DataFrame,
    predictions: pd.DataFrame,
    metrics: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(OUTPUT_DIR / "predictions_sample.csv", index=False)
    metrics.to_csv(OUTPUT_DIR / "metrics.csv", index=False)

    plt.figure(figsize=(11, 5))
    plt.plot(predictions["target_ts"], predictions["actual"], label="Actual", marker="o")
    plt.plot(
        predictions["target_ts"],
        predictions["baseline_prediction"],
        label="Baseline",
        linestyle="--",
    )
    plt.plot(
        predictions["target_ts"],
        predictions["model_prediction"],
        label="Linear Regression",
        marker=".",
    )
    plt.title("Next-hour temperature: actual vs predictions")
    plt.xlabel("Target hour")
    plt.ylabel("Temperature, C")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "predictions.png", dpi=160)
    plt.close()

    figure, axes = plt.subplots(1, 2, figsize=(11, 5))
    metrics.set_index("model")[["MAE", "RMSE"]].plot(kind="bar", rot=0, ax=axes[0])
    axes[0].set_title("Error metrics, C")
    axes[0].set_ylabel("Lower is better")
    metrics.set_index("model")[["R2"]].plot(kind="bar", rot=0, ax=axes[1])
    axes[1].set_title("R2")
    axes[1].set_ylabel("Higher is better")
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "metrics.png", dpi=160)
    plt.close(figure)

    baseline_mae = metrics.loc[metrics["model"] == "Baseline", "MAE"].iloc[0]
    model_mae = metrics.loc[metrics["model"] == "Linear Regression", "MAE"].iloc[0]
    conclusion = (
        "Linear Regression is better than the mean baseline by MAE."
        if model_mae < baseline_mae
        else "Linear Regression is not better than the mean baseline by MAE."
    )
    metric_rows = "\n".join(
        f'| {row["model"]} | {row["MAE"]:.4f} | {row["RMSE"]:.4f} | {row["R2"]:.4f} |'
        for _, row in metrics.iterrows()
    )
    summary = f"""# Week 13 ML Summary

## Task

Predict Tokyo temperature for the next hour. Features contain only information
available at hour `t`; the target is temperature at hour `t+1`.

## Leakage Protection

- target is shifted one hour into the future and is not included in features;
- rows are sorted by timestamp;
- the first 80% of observations form train and the last 20% form test;
- no preprocessing is fitted on the test set.

## Data Split

- input rows: {len(train) + len(test)}
- train rows: {len(train)}, period: {train["ts"].min()} to {train["ts"].max()}
- test rows: {len(test)}, period: {test["ts"].min()} to {test["ts"].max()}
- features: {", ".join(FEATURES)}

## Metrics

| Model | MAE | RMSE | R2 |
|---|---:|---:|---:|
{metric_rows}

MAE is the average absolute prediction error in degrees Celsius. RMSE penalizes
large errors more strongly. R2 compares the model with prediction by the test
mean; values below zero indicate poor generalization.

## Conclusion

{conclusion} However, R2 is close to zero, so the model explains almost none of
the variation beyond a constant prediction. The dataset covers only seven days,
so metrics are not stable enough for production use. More historical data and
comparison with a stronger time-series baseline are required.
"""
    (OUTPUT_DIR / "week13_summary.md").write_text(summary, encoding="utf-8")


def main() -> None:
    df = build_model_dataset()
    train, test = split_by_time(df)
    X_train, y_train = train[FEATURES], train[TARGET]
    X_test, y_test = test[FEATURES], test[TARGET]

    baseline = DummyRegressor(strategy="mean").fit(X_train, y_train)
    model = LinearRegression().fit(X_train, y_train)
    baseline_prediction = baseline.predict(X_test)
    model_prediction = model.predict(X_test)

    metrics = pd.DataFrame(
        [
            {"model": "Baseline", **regression_metrics(y_test, baseline_prediction)},
            {
                "model": "Linear Regression",
                **regression_metrics(y_test, model_prediction),
            },
        ]
    )
    predictions = pd.DataFrame(
        {
            "feature_ts": test["ts"],
            "target_ts": test["target_ts"],
            "actual": y_test,
            "baseline_prediction": baseline_prediction,
            "model_prediction": model_prediction,
        }
    )
    save_artifacts(train, test, predictions, metrics)

    print(f"[INFO] input: {INPUT_PATH}")
    print(f"[INFO] train rows: {len(train)}, test rows: {len(test)}")
    print(metrics.to_string(index=False))
    print(f"[OK] artifacts saved: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
