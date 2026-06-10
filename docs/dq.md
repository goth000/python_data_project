# Data Quality Rules

## Проверяемый слой

DQ-проверки выполняются для аналитической витрины `mart` перед загрузкой в PostgreSQL.
Скрипт `src/pipeline/dq.py` получает путь к текущей витрине от pipeline или читает его
из `data/state/state_variant_06.json`.

Правила хранятся в `configs/variant_06.yml` в структурированном блоке `dq_rules`.
Код читает из конфига тип проверки, поля, допустимые границы и критичность.

## Статусы

| Status | Meaning |
|---|---|
| PASS | Проверка успешно пройдена |
| WARNING | Найдено мягкое нарушение; pipeline может продолжить работу |
| FAIL | Найдено критичное нарушение; pipeline останавливается до load |

## Правила

| Rule | Severity | Violation |
|---|---|---|
| non_empty | critical | Витрина пустая |
| not_null_date | critical | В `date` есть NULL |
| not_null_city_id | critical | В `city_id` есть NULL |
| unique_business_key | critical | Есть дубли по `date + city_id` |
| temperature_range | warning | `t_mean` вне диапазона `[-80; 60]` °C |
| non_negative_precipitation | critical | `precipitation_sum < 0` |
| non_negative_wind | warning | `wind_speed_max < 0` |

Business key витрины: `date + city_id`.

## Запуск и отчёт

```cmd
conda run -n python_data_project_env python src/pipeline/dq.py
```

Результат сохраняется в `docs/dq_report.json`. Отчёт содержит проверяемый датасет,
сводное количество `PASS`, `WARNING`, `FAIL` и детали каждой проверки.

## Unit Tests

Тесты находятся в `tests/test_dq.py` и покрывают позитивный, негативный, граничный
сценарии, а также различие между `WARNING` и критичным `FAIL`.

Диагностический файл `broken_assert.py` показывает, почему `df["x"].notna` без
скобок даёт ложный PASS и почему нужно использовать `df["x"].notna().all()`.
