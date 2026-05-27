import pandas as pd

from src.pipeline.dq import (
    check_non_empty,
    check_not_null,
    check_temperature_range,
)


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
        "t_mean": [-100, 0, 100]
    })

    result = check_temperature_range(df)

    assert result["status"] == "PASS"