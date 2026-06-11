# Python Data Project

## Project Overview

Проект реализует полный учебный Data Engineering Pipeline для обработки исторических погодных данных Open-Meteo по городу Токио.

Источник данных:

* Open-Meteo Archive API

Цель проекта:

* получать погодные данные из API;
* сохранять исходные данные;
* выполнять очистку и нормализацию;
* строить аналитическую витрину;
* загружать данные в PostgreSQL;
* выполнять проверки качества данных;
* визуализировать данные через Metabase Dashboard.

Полный поток данных:

```text
Open-Meteo API
        ↓
RAW JSON
        ↓
NORMALIZED CSV
        ↓
MART CSV
        ↓
PostgreSQL
        ↓
Metabase Dashboard
```

---

# Repository Structure

```text
configs/                 YAML конфигурации

data/
├── raw/                 исходные JSON ответы API
├── normalized/          очищенные табличные данные
├── mart/                аналитические витрины
└── state/               pipeline state и watermark

docs/
├── bi/                  скриншоты BI dashboard
├── figures/             графики визуализации
├── llm/                 проверяемая LLM-сводка и контекст
├── ml/                  ML-метрики и прогнозы
├── Data_Contract.md
├── Implementation_Plan.md
├── LLM_Usage_Log.md
├── sql_checks.md
├── data_dictionary.md
├── dq.md
└── dq_report.json

notebooks/
├── week3_eda.ipynb
└── week7_viz.ipynb

reference/
├── cities.csv

scripts/
├── setup_env.bat

src/pipeline/
├── extract.py
├── normalize.py
├── mart.py
├── load.py
├── dq.py
├── schema_check.py
└── pipeline.py

src/analytics/
├── week13_ml.py
└── llm_summary.py

tests/
├── test_dq.py
├── test_week13_ml.py
└── test_llm_summary.py

docker-compose.yml
requirements.txt
README.md
```

---

# Technology Stack

* Python 3.11
* Pandas
* Requests
* PyYAML
* PostgreSQL
* SQLAlchemy
* Psycopg2
* Matplotlib
* Pytest
* Docker
* Docker Compose
* Metabase
* Conda

---

# Environment Setup

## Windows + Conda

Открыть Anaconda Prompt в корне проекта:

```cmd
scripts\setup_env.bat
```

Скрипт автоматически:

* проверяет Conda;
* создаёт окружение;
* устанавливает зависимости;
* запускает smoke test.

---

# Smoke Test

Ожидаемый результат:

```text
python: ...
pandas: ...
[OK] Environment is ready.
```

---

# Week 1 — Project Bootstrap

Реализовано:

* структура репозитория;
* настройка окружения через Conda;
* requirements.txt;
* setup_env.bat;
* smoke test;
* README.

---

# Week 2 — Extract Layer

Реализовано:

* чтение YAML-конфига;
* получение данных из Open-Meteo API;
* timeout и обработка ошибок;
* сохранение RAW JSON;
* логирование загрузки.

conda run -n python_data_project_env python src/pipeline/extract.py

Основной скрипт:

```text
src/pipeline/extract.py
```

RAW данные сохраняются в:

```text
data/raw/variant_06/
```

---

# Week 3 — Normalize Layer

Реализовано:

* преобразование JSON → DataFrame;
* работа с типами данных;
* очистка данных;
* удаление дублей;
* создание normalized слоя.

Основной скрипт:

```text
src/pipeline/normalize.py
```

Результат:

```text
data/normalized/variant_06/
```

---

# Week 4 — Mart Layer

Реализовано построение аналитической витрины.

Основные KPI:

* t_mean
* t_max
* precipitation_sum
* rainy_hours
* wind_speed_max

Основной скрипт:

```text
src/pipeline/mart.py
```

Результат:

```text
data/mart/variant_06/
```

---

# Week 5 — PostgreSQL

Реализована загрузка MART слоя в PostgreSQL.

Основной скрипт:

```text
src/pipeline/load.py
```

Таблица:

```text
mart_open_meteo
```

Дополнительно:

```text
docs/sql_checks.md
```

содержит SQL проверки качества данных.

---

# Week 6 — ETL Pipeline

Реализован единый запуск пайплайна.

Основной скрипт:

```text
src/pipeline/pipeline.py
```

Поддерживаются:

* full load;
* incremental load;
* state management;
* watermark.

State хранится в:

```text
data/state/state_variant_06.json
```

Запуск полного режима:

```cmd
conda run -n python_data_project_env python -m src.pipeline.pipeline --config configs/variant_06.yml --mode full
```

Запуск инкрементального режима:

```cmd
conda run -n python_data_project_env python -m src.pipeline.pipeline --config configs/variant_06.yml --mode incremental
```

`incremental` читает `last_watermark`, запрашивает только даты после него и
транзакционно заменяет только новый период в PostgreSQL. Если новых дат нет,
пайплайн завершается без создания новых RAW, NORMALIZED и MART файлов.

---

# Week 7 — Visualization

Создан notebook визуального анализа.

Notebook:

```text
notebooks/week7_viz.ipynb
```

Построены:

* Time Series Chart;
* Distribution Chart;
* Ranking Chart;
* Broken Dates Diagnostic.

PNG графики:

```text
docs/figures/
```

---

# Week 8 — Data Quality

Реализованы автоматические проверки качества данных.

Основной скрипт:

```text
src/pipeline/dq.py
```

Проверки:

* non_empty;
* not_null_date;
* not_null_city_id;
* unique_business_key;
* temperature_range;
* non_negative_precipitation;
* non_negative_wind.

Отчёт сохраняется:

```text
docs/dq_report.json
```

Также реализованы:

```text
tests/test_dq.py
```

Проверки запускаются через:

```cmd
conda run -n python_data_project_env python -m pytest
```

---

# Week 9 — Data Governance

Реализованы:

* Data Dictionary;
* Schema Validation;
* Unit Conversion Validation.

Документы:

```text
docs/data_dictionary.md
```

Проверка схемы:

```text
src/pipeline/schema_check.py
```

Сверка mart и normalized с машинным контрактом:

```cmd
conda run -n python_data_project_env python src/pipeline/schema_check.py --layer mart
conda run -n python_data_project_env python src/pipeline/schema_check.py --layer normalized
```

Диагностический скрипт:

```text
broken_units.py
```

---

# Week 10 — Docker & BI

Реализован локальный воспроизводимый аналитический стенд.

Используются сервисы:

* PostgreSQL
* Metabase

Конфигурация:

```text
docker-compose.yml
```

Запуск:

```cmd
docker compose up -d
docker compose ps
```

Проверка volumes:

```cmd
docker volume ls
```

Используемые volumes:

```text
pgdata
metabase_data
```

`docker compose stop` останавливает существующие контейнеры, а `start` запускает
их снова. `docker compose down` удаляет контейнеры и сеть, но сохраняет named
volumes. Команда `docker compose down -v` дополнительно удаляет volumes и данные.

PostgreSQL доступен локальному Python-коду через `localhost:5432`. Metabase
работает внутри Compose-сети и подключается к PostgreSQL по имени сервиса
`postgres:5432`. Dashboard читает таблицу `mart_open_meteo` из PostgreSQL, а не
CSV-файл.

Проверка persistence и mounts описана в:

```text
docs/bi/week10_validation.md
```

---

# Metabase Dashboard

Metabase доступен:

```text
http://localhost:3000
```

Построен Dashboard:

```text
Tokyo Weather Dashboard
```

Включает:

* Temperature Trend
* Rainfall Ranking
* Max Temperature

Скриншоты:

```text
docs/bi/
├── dashboard_overview.png
├── chart_timeseries.png
├── chart_ranking.png
└── docker_compose_ps.png
```

---

# Data Quality & Governance Artifacts

Документация проекта:

```text
docs/Data_Contract.md
docs/Implementation_Plan.md
docs/LLM_Usage_Log.md
docs/sql_checks.md
docs/data_dictionary.md
docs/dq.md
```

---

# Diagnostic Scripts

В проекте присутствуют учебные diagnostic scripts:

```text
broken_env.py
broken_requests.py
broken_pandas_read.py
broken_merge.py
broken_append.py
broken_dates_plot.py
broken_assert.py
broken_commit.py
broken_units.py
```

Используются для демонстрации типовых ошибок Data Engineering пайплайнов.

---

# Running The Project

Подготовка окружения:

```cmd
scripts\setup_env.bat
```

Финальный воспроизводимый сценарий:

```cmd
scripts\final_run.bat
```

Скрипт автоматически запускает и ожидает PostgreSQL, затем последовательно
выполняет full pipeline, ML-анализ, проверяемую LLM-сводку и тесты.

BI и Airflow:

```cmd
docker compose up -d
docker compose ps
```
# Week11 Airflow Orchestration

На 11 неделе ETL pipeline был перенесён под управление Apache Airflow.

## Цель

Автоматизировать выполнение всех этапов ETL и обеспечить их последовательный запуск по расписанию.

Pipeline выполняется в следующем порядке:

```text
extract
   ↓
transform
   ↓
load
   ↓
dq
```

Каждая следующая задача запускается только после успешного завершения предыдущей.

В checkpoint недели 11 сохранён именно этот порядок. В основном репозитории
используется доработанный вариант следующей недели, где DQ является блокирующей
проверкой перед загрузкой: `extract -> transform -> dq -> load`.

---

## Airflow Infrastructure

Airflow запускается в Docker Compose вместе с PostgreSQL и Metabase.

Используемые сервисы:

```text
postgres
metabase
airflow-db
airflow-scheduler
airflow-webserver
```

Проверка состояния сервисов:

```cmd
docker compose ps
```

Airflow Web UI:

```text
http://localhost:8080
```

Логин:

```text
airflow
```

Пароль:

```text
airflow
```

## Schedule Diagnostics

Диагностический DAG `airflow/dags/broken_dag.py` намеренно использует
`start_date=datetime.now()`, расписание `@daily` и `catchup=True`. Такой
`start_date` вычисляется заново при каждом чтении файла, поэтому граница
планирования постоянно сдвигается. Вместе с `catchup=True` это делает создание
ожидаемых исторических запусков непредсказуемым.

Исправленный DAG `airflow/dags/fixed_dag.py` использует фиксированный прошедший
`start_date` в UTC, частое расписание и `catchup=False`. `schedule` определяет
границы data interval, `start_date` задаёт начало планирования, а `catchup`
решает, создавать ли пропущенные интервалы между началом и текущим временем.

---

## DAG

Основной DAG проекта:

```text
airflow/dags/etl_variant_06.py
```

Задачи DAG:

### extract

Получение данных Open-Meteo API.

Скрипт:

```text
src/pipeline/extract.py
```

### transform

Нормализация данных и построение витрины.

Скрипты:

```text
src/pipeline/normalize.py
src/pipeline/mart.py
```

### load

Загрузка витрины в PostgreSQL.

Скрипт:

```text
src/pipeline/load.py
```

### dq

Проверка качества данных после загрузки.

Скрипт:

```text
src/pipeline/dq.py
```

Каждый дневной запуск DAG обрабатывает дату из `data_interval_start` и использует
собственные RAW, normalized и mart-файлы с датой начала интервала в имени. Это
не позволяет повторным или историческим запускам случайно обработать файл другого периода.
`max_active_runs=1` дополнительно ограничивает DAG одним активным запуском.

Пути, записанные в state-файл, сохраняются в POSIX-формате. Проверки также
поддерживают старые пути с разделителями Windows, поэтому pipeline одинаково
работает локально и внутри Linux-контейнеров Airflow.

---

## PostgreSQL Integration

Для работы внутри Docker-сети Airflow использует имя сервиса Postgres:

```text
postgres
```

а не:

```text
localhost
```

Подключение передается через переменные окружения:

```text
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
```

Это позволяет одному и тому же коду работать как локально, так и внутри контейнеров.

---

## Data Quality

После загрузки данных автоматически запускаются проверки качества данных.

Проверяются:

* наличие строк;
* отсутствие пустых значений в ключевых полях;
* корректность структуры витрины;
* готовность данных для аналитики.

---

## Airflow Artifacts

Скриншоты работы Airflow находятся в:

```text
docs/airflow/
```

Содержимое:

```text
docs/airflow/
├── airflow_dags.png
├── airflow_graph.png
├── docker_compose_ps.png
├── week12_airflow_dags.png
├── week12_airflow_graph.png
└── week12_validation.md
```

---

## Result

К завершению недели реализован полностью автоматизированный ETL pipeline:

```text
Open-Meteo API
        ↓
      RAW
        ↓
   NORMALIZED
        ↓
      MART
        ↓
   PostgreSQL
        ↓
  Data Quality
```

Управление выполнением осуществляется через Apache Airflow.

## Week 12 — Period-aware Airflow

Основной DAG работает по дневным data interval и передает дату периода в
Open-Meteo API. Порядок `extract -> transform -> dq -> load` делает DQ
блокирующей проверкой до загрузки.

Load запускается в режиме `incremental`: в одной транзакции удаляет и повторно
вставляет только загружаемый период. Уникальный индекс `(date, city_id)`
дополнительно защищает таблицу от дублей. Поэтому retry, clear и повторный
исторический запуск одного периода не удваивают данные.

## Week 13 — ML Basics and Data Leakage

В `notebooks/week13_ml.ipynb` показаны типичные ошибки leakage и их исправление.
Дополнительный воспроизводимый сценарий находится в
`src/analytics/week13_ml.py`: по данным часа `t` он прогнозирует температуру
часа `t+1`, использует только прошлую информацию и выполняет time-based split.

Сравниваются `DummyRegressor(strategy="mean")` и `LinearRegression`.
Linear Regression получила MAE около `0.73°C` против `2.64°C` у baseline, но
`R²` около нуля показывает ограниченную практическую ценность на истории всего
за семь дней.

Артефакты сохранены в `docs/ml/`:

```text
week13_summary.md
predictions_sample.csv
metrics.csv
predictions.png
metrics.png
```

## Week 14 — Verifiable LLM Summary

LLM используется только как интерпретационный слой после pipeline, DQ, BI и
ML. Скрипт `src/analytics/llm_summary.py` кодом рассчитывает агрегаты из MART,
добавляет DQ summary и сохраняет ограниченный контекст:

```text
docs/llm/context.json
```

Offline-сводка сохраняется в `docs/llm/summary.md`. Валидатор проверяет, что в
ней отсутствуют числа, которых нет в рассчитанном контексте, и сохраняет
результат в `docs/llm/validation.json`.

Настоящий API-ключ не требуется и не хранится в репозитории. Для возможной
будущей интеграции предоставлен `.env.example`; реальные значения должны
находиться только в игнорируемом `.env`.
