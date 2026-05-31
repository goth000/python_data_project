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

tests/
├── test_dq.py

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

Полный запуск ETL:

```cmd
conda run -n python_data_project_env python src/pipeline/pipeline.py
```

Загрузка в PostgreSQL:

```cmd
conda run -n python_data_project_env python src/pipeline/load.py
```

DQ проверки:

```cmd
conda run -n python_data_project_env python src/pipeline/dq.py
```

Schema validation:

```cmd
conda run -n python_data_project_env python src/pipeline/schema_check.py
```

Pytest:

```cmd
conda run -n python_data_project_env python -m pytest
```

Docker:

```cmd
docker compose up -d
docker compose ps
```
