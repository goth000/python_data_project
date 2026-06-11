# Data Contract

**Contract version:** 1.4

**Variant:** 06

**Source:** Open-Meteo Archive API

**Entity:** Tokyo (`JP_TYO`)

**Timezone:** Asia/Tokyo

## Общие правила

- колонки используют `snake_case`;
- идентификаторы заканчиваются на `_id`;
- RAW хранит исходный ответ без преобразований;
- NORMALIZED содержит одно почасовое наблюдение города;
- MART содержит один дневной агрегат города;
- единицы и timezone не изменяются неявно;
- обязательные поля не допускают NULL;
- изменения контракта фиксируются в changelog.

---

## Week 1 — Структура слоев

| Layer | Назначение |
|---|---|
| `data/raw/` | исходные ответы API |
| `data/normalized/` | типизированные наблюдения |
| `data/mart/` | аналитические агрегаты |
| `data/state/` | watermark и служебное состояние |

## Week 2 — RAW

| Property | Value |
|---|---|
| Method | GET |
| Endpoint | `https://archive-api.open-meteo.com/v1/archive` |
| Period parameters | `start_date`, `end_date` |
| Coordinates | `35.6762`, `139.6503` |
| Timezone | `Asia/Tokyo` |
| Required hourly arrays | temperature, humidity, precipitation, wind |

RAW сохраняется как полученный JSON. Одна запись массива `hourly.time`
соответствует значениям с тем же индексом во всех hourly-массивах.

## Week 3 — NORMALIZED

Гранулярность: **одно почасовое наблюдение одного города**.

Бизнес-ключ: `city_id + ts`.

| Column | Type | Nullable | Unit | Meaning |
|---|---|---:|---|---|
| `ts` | datetime | no | Asia/Tokyo local time | время наблюдения |
| `temperature_2m` | float | no | °C | температура на высоте 2 м |
| `relative_humidity_2m` | integer | no | % | относительная влажность |
| `precipitation` | float | no | mm/hour | осадки за час |
| `wind_speed_10m` | float | no | km/h | скорость ветра |
| `city_id` | string | no | none | идентификатор города |

Правила: валидное datetime, numeric conversion, отсутствие NULL, удаление
дублей по бизнес-ключу, сортировка по `city_id + ts`.

## Week 4 — MART

Гранулярность: **один дневной агрегат одного города**.

Бизнес-ключ: `date + city_id`.

| Column | Type | Nullable | Unit | Meaning |
|---|---|---:|---|---|
| `date` | date | no | YYYY-MM-DD | дата агрегации |
| `city_id` | string | no | none | идентификатор города |
| `city_name` | string | no | none | название города |
| `country_code` | string | no | ISO alpha-2 | код страны |
| `timezone` | string | no | IANA timezone | timezone наблюдений |
| `t_mean` | float | no | °C | средняя температура за день |
| `t_max` | float | no | °C | максимальная температура за день |
| `precipitation_sum` | float | no | mm | сумма осадков за день |
| `rainy_hours` | integer | no | hours | часы с `precipitation > 0` |
| `wind_speed_max` | float | no | km/h | максимальный ветер за день |

Join со справочником `reference/cities.csv` выполняется как `many_to_one` по
`city_id`; число строк после join не должно изменяться.

## Week 5 — PostgreSQL

| Property | Contract |
|---|---|
| Database | PostgreSQL / `analytics` |
| Table | `mart_open_meteo` |
| Business key | `date + city_id` |
| Full strategy | replace |
| Incremental strategy | delete period + append in one transaction |

Таблица не должна содержать NULL в бизнес-ключе или дубли.

## Week 6 — State и incremental

Файл `data/state/state_variant_06.json` содержит:

| Field | Meaning |
|---|---|
| `variant_id` | вариант проекта |
| `source_type` | тип источника |
| `mode` | последний режим запуска |
| `last_watermark` | последняя успешно обработанная дата |
| `business_key` | ключ MART |
| `last_mart_file` | относительный путь последнего MART |
| `last_successful_run` | время успешного завершения |

State обновляется атомарно только после успешного DQ и load.

## Week 7 — Visualization

Графики используют MART. Временная колонка преобразуется в datetime и
сортируется по календарному времени. Оси содержат название метрики и единицу.

## Week 8 — Data Quality

| Rule | Severity | Contract |
|---|---|---|
| `non_empty` | critical | MART содержит строки |
| `not_null_date` | critical | `date` без NULL |
| `not_null_city_id` | critical | `city_id` без NULL |
| `unique_business_key` | critical | нет дублей `date + city_id` |
| `temperature_range` | warning | `t_mean` в `[-80; 60]` °C |
| `non_negative_precipitation` | critical | `precipitation_sum >= 0` |
| `non_negative_wind` | warning | `wind_speed_max >= 0` |

Критичный FAIL завершает DQ ненулевым кодом и блокирует load.

## Week 9 — Governance

Машиночитаемые схемы находятся в `configs/variant_06.yml`.
`src/pipeline/schema_check.py` проверяет колонки, порядок, типы и nullable.
Человеко-ориентированные определения находятся в `docs/data_dictionary.md`.

## Week 10 — BI

Metabase читает `mart_open_meteo` из PostgreSQL, а не CSV. PostgreSQL и
Metabase используют named volumes; данные должны переживать пересоздание
контейнеров без `down -v`.

## Week 11 — Airflow orchestration

Airflow запускает стадии в явно заданном порядке. Каждый task обязан завершаться
ненулевым кодом при ошибке и писать в лог период, пути и количество строк.

## Week 12 — Period-aware execution

Один DAG run обрабатывает один дневной `data_interval`. RAW, NORMALIZED и MART
имеют отдельные пути периода. Порядок:

```text
extract -> transform -> dq -> load
```

Повтор одного периода заменяет строки этого периода и не создает дублей.

## Week 13 — ML dataset

Target: `temperature_2m` следующего часа. Target не входит в признаки.
Данные сортируются по `ts`; train содержит прошлое, test — будущее. Метрики и
predictions сохраняются в `docs/ml/`.

## Week 14 — LLM report contract

LLM получает только:

- identity набора и период;
- рассчитанные кодом агрегаты;
- DQ summary;
- ограничения на интерпретацию.

RAW и приватные данные не передаются. Любое число в summary должно существовать
в `docs/llm/context.json`; иначе validation получает FAIL.

---

## Changelog

| Version | Week | Change |
|---|---:|---|
| 0.1 | 1 | создана структура слоев |
| 0.2 | 2 | добавлен RAW API contract |
| 0.3 | 3 | добавлена NORMALIZED schema |
| 0.4 | 4 | добавлена MART schema и join cardinality |
| 0.5 | 5 | добавлен PostgreSQL contract |
| 0.6 | 6 | добавлены state и incremental правила |
| 0.7 | 7 | добавлены правила визуализации времени |
| 0.8 | 8 | добавлены DQ rules и severity |
| 0.9 | 9 | добавлены governance и schema validation |
| 1.0 | 10 | добавлен BI contract |
| 1.1 | 11 | добавлен Airflow task contract |
| 1.2 | 12 | добавлен period-aware и retry-safe contract |
| 1.3 | 13 | добавлен ML dataset contract |
| 1.4 | 14 | добавлен проверяемый LLM report contract |
