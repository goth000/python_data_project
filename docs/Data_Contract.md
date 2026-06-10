# Data Contract

**Contract version:** 0.9

**Variant:** 06

**Source:** Open-Meteo Archive API

**Timezone:** Asia/Tokyo

## Обзор проекта

Проект обрабатывает исторические погодные данные по Токио с использованием Open-Meteo Archive API.

Структура пайплайна:

API → RAW → NORMALIZED → MART → POSTGRES

Проект включает:
- получение данных через API;
- нормализацию данных;
- построение витрины (mart);
- загрузку в PostgreSQL;
- SQL-проверки качества данных.

---

# Week 2 — RAW слой

## Информация об источнике

| поле | значение |
|---|---|
| source_type | open_meteo |
| method | GET |
| endpoint | https://archive-api.open-meteo.com/v1/archive |

---

## Информация об объекте анализа

| поле | значение |
|---|---|
| city_id | JP_TYO |
| city_name | Tokyo |
| country_code | JP |
| timezone | Asia/Tokyo |

---

## Параметры запроса

| parameter | value |
|---|---|
| latitude | 35.6762 |
| longitude | 139.6503 |
| start_date | 2024-05-01 |
| end_date | 2024-05-07 |
| hourly | temperature_2m, relative_humidity_2m, precipitation, wind_speed_10m |

---

## Timeout

| parameter | value |
|---|---|
| timeout_sec | 10 |

---

## RAW слой

Исходные JSON-ответы API сохраняются в:

data/raw/variant_06/YYYY-MM-DD_HH-MM-SS.json

RAW слой хранит оригинальный ответ Open-Meteo API без изменений.

---

# Week 3 — NORMALIZED слой

## Normalized Dataset

Нормализованные данные строятся из RAW JSON файлов.

Файлы сохраняются в:

data/normalized/variant_06/YYYY-MM-DD_HH-MM-SS.csv

---

## Гранулярность данных

Одна строка соответствует одному часу погодных наблюдений в Токио.

---

## Схема normalized слоя

| column_name | dtype | nullable | unit | description |
|---|---|---|---|---|
| ts | datetime | no | Asia/Tokyo local time | Дата-время измерения |
| temperature_2m | float | no | °C | Температура воздуха на высоте 2 м |
| relative_humidity_2m | integer | no | % | Относительная влажность на высоте 2 м |
| precipitation | float | no | mm | Количество осадков за час |
| wind_speed_10m | float | no | km/h | Скорость ветра на высоте 10 м |
| city_id | string | no | none | Идентификатор города |

---

## Правила очистки данных

Применяются:
- преобразование datetime;
- преобразование numeric типов;
- удаление дубликатов;
- проверка пропусков.

---

# Week 4 — MART слой

## Mart Dataset

MART слой содержит агрегированные дневные KPI.

Файлы сохраняются в:

data/mart/variant_06/mart_daily_YYYY-MM-DD_HH-MM-SS.csv

---

## Гранулярность витрины

Одна строка соответствует одному дню погодных метрик по Токио.

---

## Схема mart слоя

| column_name | dtype | nullable | unit | description |
|---|---|---|---|---|
| date | date | no | YYYY-MM-DD | Дата дневной агрегации |
| city_id | string | no | none | Идентификатор города |
| city_name | string | no | none | Название города |
| country_code | string | no | ISO 3166-1 alpha-2 | Код страны |
| timezone | string | no | IANA timezone | Временная зона наблюдений |
| t_mean | float | no | °C | Средняя температура за день |
| t_max | float | no | °C | Максимальная температура за день |
| precipitation_sum | float | no | mm | Суммарное количество осадков за день |
| rainy_hours | integer | no | hours | Количество часов с осадками |
| wind_speed_max | float | no | km/h | Максимальная скорость ветра за день |

---

## Reference данные

Справочники хранятся в:

reference/

Используемый справочник:
- cities.csv

Ключ соединения:
- city_id

Тип merge:
- many_to_one

---

# Week 5 — PostgreSQL слой

## База данных

| поле | значение |
|---|---|
| database | PostgreSQL |
| host | localhost |
| port | 5432 |
| database_name | analytics |

---

## Загружаемая таблица

| поле | значение |
|---|---|
| table_name | mart_open_meteo |
| load_strategy | replace |

---

## SQL-проверки

SQL-проверки хранятся в:

docs/sql_checks.md

Проверки включают:
- проверку количества строк;
- проверку диапазона дат;
- проверку NULL значений;
- проверку дублей;
- проверку KPI;
- проверку идемпотентной загрузки._

---

# Week 6 — Pipeline, State и Incremental Processing

## ETL Pipeline

Проект использует ETL pipeline:

```text
Extract → Normalize → Mart → Load
```

Pipeline scripts:

```text
src/pipeline/extract.py
src/pipeline/normalize.py
src/pipeline/mart.py
src/pipeline/load.py
src/pipeline/pipeline.py
```

---

## Единая точка входа

Pipeline запускается через:

```cmd
conda run -n python_data_project_env python -m src.pipeline.pipeline --config configs/variant_06.yml --mode full
```

или:

```cmd
conda run -n python_data_project_env python -m src.pipeline.pipeline --config configs/variant_06.yml --mode incremental
```

---

## Инкрементальная обработка

Поддерживаются режимы:

| mode | description |
|---|---|
| full | полная переработка данных |
| incremental | обработка только новых данных |

---

В режиме `incremental` пайплайн читает `last_watermark` из state и вычисляет
начало следующего периода как `last_watermark + 1 день`. Конец периода берётся
из `api.params.end_date` выбранного конфига. Если новых дат нет, запуск
завершается без повторного создания артефактов.

При загрузке нового периода строки этого периода удаляются и вставляются заново
в одной PostgreSQL-транзакции. Исторические периоды не перезаписываются.

---

## Watermark

Используемый watermark:

```text
last_watermark
```

Пример значения:

```text
2024-05-07
```

---

## State Pipeline

Pipeline сохраняет state:

```text
data/state/state_variant_06.json
```

State обновляется атомарно и только после успешного завершения `load`.
`last_mart_file` сохраняется как относительный путь внутри проекта.

State содержит:
- watermark;
- последний mart файл;
- время последнего запуска;
- режим запуска pipeline.

---

## Business Key

Business key витрины:

```text
date + city_id
```

Каждая комбинация даты и города должна быть уникальной.

---

## Идемпотентность

Pipeline реализован идемпотентно:
- повторный запуск не создает логических дублей;
- mart пересобирается заново;
- PostgreSQL использует стратегию `replace`.

---

# Week 7 — Visualization и Time Series

## Visualization Layer

Для визуального анализа используется notebook:

```text
notebooks/week7_viz.ipynb
```

---

## Используемые графики

В проекте реализованы:

| graph_type | description |
|---|---|
| time series | изменение температуры во времени |
| histogram | распределение средней температуры |
| ranking bar chart | ranking осадков по дням |

---

## Time Handling

Перед построением графиков колонка `date` преобразуется:

```python
pd.to_datetime(df["date"])
```

Это необходимо для корректной сортировки временной оси.

---

## Timezone

Все временные данные интерпретируются в timezone:

```text
Asia/Tokyo
```

---

## Visualization Outputs

PNG графики сохраняются в:

```text
docs/figures/
```

---

# Week 8 — Data Quality

## DQ Layer

В проекте реализованы автоматические проверки качества данных.

DQ module:

```text
src/pipeline/dq.py
```

---

## DQ Report

Результаты проверок сохраняются в:

```text
docs/dq_report.json
```

---

## Реализованные DQ Checks

| check_name | description |
|---|---|
| non_empty | витрина не должна быть пустой |
| not_null_date | поле date не должно содержать NULL |
| not_null_city_id | поле city_id не должно содержать NULL |
| unique_business_key | отсутствуют дубли по business key |
| temperature_range | температура находится в допустимом диапазоне |
| non_negative_precipitation | осадки не отрицательные |
| non_negative_wind | скорость ветра не отрицательная |

---

## Unit Tests

Для DQ проверок реализованы unit tests:

```text
tests/test_dq.py
```

Тестируются:
- positive cases;
- negative cases;
- boundary cases.

---

## Diagnostic Example

Файл:

```text
broken_assert.py
```

демонстрирует ошибку использования:

```python
df["x"].notna
```

вместо:

```python
df["x"].notna().all()
```

---

# Week 9 — Data Governance

## Changelog

| version | date | change | reason |
|---|---|---|---|
| 0.1 | 2026-03 | Initial raw layer | Preserve source responses |
| 0.2 | 2026-03 | Added normalized schema | Define typed hourly observations |
| 0.3 | 2026-03 | Added mart schema | Support daily analytics |
| 0.4 | 2026-04 | Added PostgreSQL layer | Make mart queryable |
| 0.5 | 2026-04 | Added incremental processing | Process only new dates |
| 0.6 | 2026-04 | Documented visualization layer | Explain analytical outputs |
| 0.7 | 2026-04 | Added DQ checks | Detect invalid data automatically |
| 0.8 | 2026-04 | Added unit tests | Verify DQ functions |
| 0.9 | 2026-04 | Added complete schemas and governance rules | Keep contract and code aligned |

---

## Naming Rules

Используются следующие naming conventions:

| rule | description |
|---|---|
| snake_case | все колонки используют snake_case |
| *_id | идентификаторы заканчиваются на `_id` |
| date | дата хранится в поле `date` |
| запрещены value/metric1 | запрещены неоднозначные названия |
| KPI naming | KPI используют понятное имя метрики и агрегирующий суффикс: `_mean`, `_sum`, `_max`, `_hours` |

---

## Units and Semantics

| column | unit |
|---|---|
| temperature_2m | °C |
| t_mean | °C |
| t_max | °C |
| precipitation | mm |
| precipitation_sum | mm |
| wind_speed_10m | km/h |
| wind_speed_max | km/h |
| relative_humidity_2m | % |

---

## Timezone Rules

Все временные данные проекта используют timezone:

```text
Asia/Tokyo
```

Timezone фиксируется в:
- API запросах;
- normalized слое;
- mart слое;
- визуализациях;
- SQL проверках.

---

## Data Dictionary

Человеко-ориентированное описание колонок хранится в:

```text
docs/data_dictionary.md
```

---

## Contract vs Code Validation

Соответствие схемы и кода проверяется:
- вручную;
- через DQ проверки;
- через unit tests;
- через `src/pipeline/schema_check.py`, который читает схемы из `configs/variant_06.yml`
  и проверяет названия, порядок, типы и nullable для normalized и mart.

---

## Governance Risks

Типичные риски:
- ошибки единиц измерения;
- неправильная интерпретация timezone;
- silent schema changes;
- несогласованные названия колонок;
- расхождение контракта и pipeline кода.

---

## Units Conversion Validation

Файл:

```text
broken_units.py
```

демонстрирует ошибку преобразования единиц измерения и защиту через:

```python
assert
```
