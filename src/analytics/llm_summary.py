import argparse
import json
import os
import re
from datetime import date
from pathlib import Path

import pandas as pd
import requests
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MART_PATH = (
    PROJECT_ROOT / "data" / "mart" / "variant_06" / "mart_daily_2026-05-27_17-55-59.csv"
)
DEFAULT_DQ_PATH = PROJECT_ROOT / "docs" / "dq_report.json"
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "variant_06.yml"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "llm"
CONTEXT_PATH = OUTPUT_DIR / "context.json"
SUMMARY_PATH = OUTPUT_DIR / "summary.md"
VALIDATION_PATH = OUTPUT_DIR / "validation.json"


def load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def round_metric(value: float) -> float:
    return round(float(value), 2)


def build_context(mart_path: Path, dq_path: Path, config_path: Path) -> dict:
    mart = pd.read_csv(mart_path, parse_dates=["date"]).sort_values("date")
    if mart.empty:
        raise ValueError("MART must not be empty")

    config = load_yaml(config_path)
    dq_report = load_json(dq_path)
    max_wind_row = mart.loc[mart["wind_speed_max"].idxmax()]
    rainy_row = mart.loc[mart["precipitation_sum"].idxmax()]

    return {
        "dataset_identity": {
            "variant_id": str(config["variant_id"]).zfill(2),
            "source": config["source_type"],
            "city_id": config["entity"]["city_id"],
            "city_name": config["entity"]["city_name"],
            "timezone": config["entity"]["timezone"],
            "period_start": mart["date"].min().date().isoformat(),
            "period_end": mart["date"].max().date().isoformat(),
            "row_count": int(len(mart)),
            "row_meaning": "one daily weather aggregate for one city",
        },
        "computed_metrics": {
            "temperature_mean_c": round_metric(mart["t_mean"].mean()),
            "temperature_min_c": round_metric(mart["t_mean"].min()),
            "temperature_max_c": round_metric(mart["t_mean"].max()),
            "precipitation_total_mm": round_metric(mart["precipitation_sum"].sum()),
            "rainy_hours_total": int(mart["rainy_hours"].sum()),
            "max_wind_speed_kmh": round_metric(mart["wind_speed_max"].max()),
            "max_wind_date": max_wind_row["date"].date().isoformat(),
            "wettest_date": rainy_row["date"].date().isoformat(),
            "wettest_day_precipitation_mm": round_metric(
                rainy_row["precipitation_sum"]
            ),
        },
        "quality_status": {
            status: int(dq_report["summary"][status])
            for status in ["PASS", "WARNING", "FAIL"]
        },
        "constraints": [
            "Use only the provided computed metrics.",
            "Do not invent or calculate new numbers.",
            "If the context is insufficient, state that it is insufficient.",
            "Treat explanations of causes as hypotheses, not facts.",
        ],
    }


def render_offline_summary(context: dict) -> str:
    identity = context["dataset_identity"]
    metrics = context["computed_metrics"]
    quality = context["quality_status"]
    return f"""# Проверяемая LLM-сводка

## Контекст

Набор содержит {identity["row_count"]} дневных строк по городу
{identity["city_name"]} за период {identity["period_start"]} — {identity["period_end"]}.
Все числа ниже заранее рассчитаны кодом и переданы как ограниченный контекст.

## Рассчитанные показатели

- средняя дневная температура: {metrics["temperature_mean_c"]} °C;
- минимальная дневная температура: {metrics["temperature_min_c"]} °C;
- максимальная дневная температура: {metrics["temperature_max_c"]} °C;
- суммарные осадки: {metrics["precipitation_total_mm"]} мм;
- дождливые часы: {metrics["rainy_hours_total"]};
- максимальная скорость ветра: {metrics["max_wind_speed_kmh"]} км/ч,
  дата: {metrics["max_wind_date"]};
- максимальные суточные осадки: {metrics["wettest_day_precipitation_mm"]} мм,
  дата: {metrics["wettest_date"]}.

## Качество данных

DQ: PASS={quality["PASS"]}, WARNING={quality["WARNING"]}, FAIL={quality["FAIL"]}.

## Интерпретация

Период короткий, поэтому устойчивый сезонный тренд определить нельзя.
День с максимальными осадками и день с максимальным ветром стоит рассмотреть
отдельно как возможные погодные события. Причины этих событий из переданного
контекста установить нельзя.

## Ограничения

Сводка не вычисляет новые показатели и не делает причинных выводов. Для
надёжного анализа требуется более длинная история.
"""


def build_prompt(context: dict) -> str:
    return (
        "Create a short Markdown analytical summary in Russian. "
        "Use only the provided context. Do not invent or calculate numbers. "
        "If data is insufficient, say so. Treat causes only as hypotheses.\n\n"
        + json.dumps(context, ensure_ascii=False, indent=2)
    )


def request_online_summary(context: dict) -> str:
    api_url = os.environ.get("LLM_API_URL")
    api_key = os.environ.get("LLM_API_KEY")
    model = os.environ.get("LLM_MODEL")
    if not api_url or not api_key or not model:
        raise ValueError("Online mode requires LLM_API_URL, LLM_API_KEY and LLM_MODEL")

    response = requests.post(
        api_url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You interpret provided metrics and never invent numbers.",
                },
                {"role": "user", "content": build_prompt(context)},
            ],
            "temperature": 0,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def collect_allowed_numeric_tokens(value) -> set[str]:
    tokens: set[str] = set()
    if isinstance(value, dict):
        for item in value.values():
            tokens.update(collect_allowed_numeric_tokens(item))
    elif isinstance(value, list):
        for item in value:
            tokens.update(collect_allowed_numeric_tokens(item))
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        tokens.add(str(value))
    elif isinstance(value, (str, date)):
        tokens.update(re.findall(r"-?\d+(?:\.\d+)?", str(value)))
    return tokens


def validate_summary(summary: str, context: dict) -> dict:
    allowed_tokens = collect_allowed_numeric_tokens(context)
    summary_tokens = set(re.findall(r"-?\d+(?:\.\d+)?", summary))
    unexpected = sorted(summary_tokens - allowed_tokens)
    required_sections = [
        "# Проверяемая LLM-сводка",
        "## Рассчитанные показатели",
        "## Качество данных",
        "## Ограничения",
    ]
    missing_sections = [section for section in required_sections if section not in summary]
    return {
        "status": "PASS" if not unexpected and not missing_sections else "FAIL",
        "unexpected_numeric_tokens": unexpected,
        "missing_sections": missing_sections,
        "allowed_numeric_tokens": sorted(allowed_tokens),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a verifiable LLM-style summary")
    parser.add_argument("--mart-path", default=str(DEFAULT_MART_PATH))
    parser.add_argument("--dq-path", default=str(DEFAULT_DQ_PATH))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument(
        "--mode",
        choices=["offline", "online"],
        default=os.environ.get("LLM_MODE", "offline"),
    )
    args = parser.parse_args()

    context = build_context(Path(args.mart_path), Path(args.dq_path), Path(args.config))
    summary = (
        request_online_summary(context)
        if args.mode == "online"
        else render_offline_summary(context)
    )
    validation = validate_summary(summary, context)
    if validation["status"] != "PASS":
        raise ValueError(f"Summary validation failed: {validation}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CONTEXT_PATH.write_text(
        json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    SUMMARY_PATH.write_text(summary, encoding="utf-8")
    VALIDATION_PATH.write_text(
        json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[OK] context saved: {CONTEXT_PATH}")
    print(f"[OK] summary saved: {SUMMARY_PATH}")
    print(f"[OK] mode: {args.mode}")
    print(f"[OK] validation status: {validation['status']}")


if __name__ == "__main__":
    main()
