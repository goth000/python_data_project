import os
from pathlib import Path

import pandas as pd

from src.analytics.llm_summary import (
    build_context,
    render_offline_summary,
    validate_summary,
)
from src.pipeline.pipeline import get_latest_file


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_summary_numbers_are_limited_to_context():
    context = build_context(
        PROJECT_ROOT / "data/mart/variant_06/mart_daily_2026-05-27_17-55-59.csv",
        PROJECT_ROOT / "docs/dq_report.json",
        PROJECT_ROOT / "configs/variant_06.yml",
    )
    validation = validate_summary(render_offline_summary(context), context)

    assert validation["status"] == "PASS"
    assert validation["unexpected_numeric_tokens"] == []


def test_validator_rejects_invented_number():
    context = {
        "dataset_identity": {"row_count": 3},
        "computed_metrics": {"mean": 2.0},
        "quality_status": {"PASS": 1, "WARNING": 0, "FAIL": 0},
    }

    validation = validate_summary(
        "# Проверяемая LLM-сводка\n"
        "## Рассчитанные показатели\n"
        "Среднее 2.0, прогноз 999.\n"
        "## Качество данных\n"
        "## Ограничения\n",
        context,
    )

    assert validation["status"] == "FAIL"
    assert "999" in validation["unexpected_numeric_tokens"]


def test_context_metrics_are_calculated_by_code(tmp_path: Path):
    mart_path = tmp_path / "mart.csv"
    pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "t_mean": [10.0, 14.0],
            "precipitation_sum": [1.0, 2.0],
            "rainy_hours": [1, 2],
            "wind_speed_max": [5.0, 7.0],
        }
    ).to_csv(mart_path, index=False)
    dq_path = tmp_path / "dq.json"
    dq_path.write_text(
        '{"summary": {"PASS": 2, "WARNING": 0, "FAIL": 0}}', encoding="utf-8"
    )

    context = build_context(
        mart_path, dq_path, PROJECT_ROOT / "configs/variant_06.yml"
    )

    assert context["computed_metrics"]["temperature_mean_c"] == 12.0
    assert context["computed_metrics"]["precipitation_total_mm"] == 3.0


def test_latest_file_uses_modification_time(tmp_path: Path):
    older = tmp_path / "z_old.csv"
    newer = tmp_path / "a_new.csv"
    older.write_text("old", encoding="utf-8")
    newer.write_text("new", encoding="utf-8")
    os.utime(older, (1, 1))
    os.utime(newer, (2, 2))

    assert get_latest_file(tmp_path, "*.csv") == newer
