from pathlib import Path

import pandas as pd

from src.analytics.week13_ml import FEATURES, TARGET, build_model_dataset, split_by_time


def test_time_split_has_no_future_leakage():
    df = pd.DataFrame(
        {
            "ts": pd.date_range("2024-01-01", periods=10, freq="h"),
            TARGET: range(10),
        }
    )
    train, test = split_by_time(df)

    assert train["ts"].max() < test["ts"].min()
    assert TARGET not in FEATURES


def test_target_is_next_hour_temperature(tmp_path: Path):
    source = tmp_path / "normalized.csv"
    pd.DataFrame(
        {
            "ts": pd.date_range("2024-01-01", periods=3, freq="h"),
            "temperature_2m": [10.0, 11.0, 12.0],
            "relative_humidity_2m": [80, 81, 82],
            "precipitation": [0.0, 0.0, 0.0],
            "wind_speed_10m": [2.0, 2.0, 2.0],
        }
    ).to_csv(source, index=False)

    result = build_model_dataset(source)

    assert result[TARGET].tolist() == [11.0, 12.0]
    assert result["target_ts"].tolist() == pd.date_range(
        "2024-01-01 01:00:00", periods=2, freq="h"
    ).tolist()
