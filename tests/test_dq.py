import pandas as pd
import pytest
from sqlalchemy import create_engine, text

import src.pipeline.dq as dq_module
from src.pipeline.dq import (
    check_non_empty,
    check_not_null,
    check_non_negative_precipitation,
    check_temperature_range,
)
from src.pipeline.load import load_dataframe


def test_check_non_empty_pass():
    df = pd.DataFrame({
        "x": [1, 2, 3]
    })

    result = check_non_empty(df)

    assert result["status"] == "PASS"


def test_check_not_null_fail():
    df = pd.DataFrame({
        "x": [1, None, 3]
    })

    result = check_not_null(df, "x")

    assert result["status"] == "FAIL"


def test_temperature_range_boundary():
    df = pd.DataFrame({
        "t_mean": [-80, 0, 60]
    })

    result = check_temperature_range(df)

    assert result["status"] == "PASS"


def test_temperature_range_warning():
    df = pd.DataFrame({
        "t_mean": [61]
    })

    result = check_temperature_range(df)

    assert result["status"] == "WARNING"


def test_negative_precipitation_is_critical_fail():
    df = pd.DataFrame({
        "precipitation_sum": [-0.1]
    })

    result = check_non_negative_precipitation(df)

    assert result["status"] == "FAIL"


def test_incremental_load_is_idempotent():
    engine = create_engine("sqlite://")
    df = pd.DataFrame(
        {
            "date": [pd.Timestamp("2024-05-01").date()],
            "city_id": ["JP_TYO"],
            "t_mean": [17.1],
        }
    )

    with engine.begin() as conn:
        load_dataframe(conn, df, "incremental")
        load_dataframe(conn, df, "incremental")
        row_count = conn.execute(text("SELECT COUNT(*) FROM mart_open_meteo")).scalar()

    assert row_count == 1


def test_critical_dq_fail_exits_before_load(tmp_path, monkeypatch):
    bad_mart = tmp_path / "bad_mart.csv"
    pd.DataFrame(
        {
            "date": ["2024-05-01"],
            "city_id": ["JP_TYO"],
            "t_mean": [17.1],
            "precipitation_sum": [-1.0],
            "wind_speed_max": [10.0],
        }
    ).to_csv(bad_mart, index=False)
    monkeypatch.setattr(dq_module, "REPORT_PATH", tmp_path / "dq_report.json")
    monkeypatch.setattr(
        "sys.argv",
        [
            "dq.py",
            "--config",
            "configs/variant_06.yml",
            "--mart-path",
            str(bad_mart),
        ],
    )

    with pytest.raises(SystemExit, match="Critical DQ checks failed"):
        dq_module.main()
