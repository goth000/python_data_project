# Implementation Plan

## Цель проекта

Цель проекта — построить полноценный mini data engineering pipeline для обработки исторических погодных данных с использованием Open-Meteo API.

Пайплайн обрабатывает исторические погодные наблюдения по Токио и преобразует данные через несколько аналитических слоев:

API → RAW → NORMALIZED → MART → POSTGRES

Итоговый результат проекта:
- автоматизированное получение данных;
- нормализация и очистка;
- построение KPI;
- загрузка в PostgreSQL;
- SQL-проверки качества данных.

---

# Week 1 — Настройка окружения и репозитория

## Выполненные задачи

- Установлена Anaconda.
- Настроено Conda-окружение проекта.
- Создан reproducible setup через:

scripts/setup_env.bat

- Создан GitHub-репозиторий проекта.
- Подготовлена структура проекта:

src/
data/
docs/
configs/
tests/
scripts/
reference/
notebooks/

- Добавлен smoke-test:

broken_env.py

- Настроен requirements.txt.
- Проверен запуск через conda run.

---

# Week 2 — RAW слой и работа с API

## Цель

Построить RAW ingestion слой с использованием Open-Meteo API.

## Выполненные задачи

- Настроен YAML-конфиг источника:

configs/variant_06.yml

- Реализован extraction pipeline:

src/pipeline/extract.py

- Добавлены:
  - timeout handling;
  - проверка HTTP status;
  - проверка JSON response;
  - обработка request exceptions.

- Реализована диагностика запросов:

broken_requests.py

- RAW JSON ответы сохраняются в:

data/raw/variant_06/

## Результат

Пайплайн успешно загружает исторические погодные данные из Open-Meteo Archive API.

---

# Week 3 — NORMALIZED слой

## Цель

Преобразовать RAW JSON в табличный normalized dataset.

## Выполненные задачи

- Реализован:

src/pipeline/normalize.py

- Выполнен parsing hourly weather observations из JSON.
- Создан normalized pandas DataFrame.
- Выполнены:
  - datetime conversion;
  - numeric conversion;
  - duplicate removal;
  - missing value checks.

- Normalized CSV сохраняется в:

data/normalized/variant_06/

- Создан EDA notebook:

notebooks/week3_eda.ipynb

- Реализована диагностика pandas:

broken_pandas_read.py

## Результат

Из RAW JSON успешно построен normalized табличный dataset.

---

# Week 4 — MART слой и агрегирование

## Цель

Построить аналитическую витрину (mart) с дневными KPI.

## Выполненные задачи

- Добавлены reference datasets:

reference/cities.csv

- Реализована проверка merge:

broken_merge.py

- Реализован pipeline:

src/pipeline/mart.py

- Добавлены:
  - reference joins;
  - merge cardinality validation;
  - KPI aggregation;
  - daily time granularity.

## Рассчитанные KPI

- средняя температура за день;
- максимальная температура за день;
- сумма осадков за день;
- количество дождливых часов;
- максимальная скорость ветра.

## Результат

Построена дневная аналитическая витрина:

data/mart/variant_06/

---

# Week 5 — PostgreSQL и SQL проверки

## Цель

Загрузить MART dataset в PostgreSQL и выполнить SQL-проверки качества данных.

## Выполненные задачи

- Установлены:
  - sqlalchemy;
  - psycopg2-binary.

- Установлен и настроен Docker Desktop.
- Поднят PostgreSQL контейнер через Docker.
- Реализована диагностика транзакций:

broken_commit.py

- Реализован pipeline загрузки:

src/pipeline/load.py

- Добавлены:
  - PostgreSQL connection;
  - SQLAlchemy engine;
  - idempotent loading strategy;
  - automatic transaction handling через engine.begin().

- MART dataset загружается в таблицу PostgreSQL:

mart_open_meteo

- Созданы SQL проверки:

docs/sql_checks.md

## SQL проверки включают

- проверку количества строк;
- проверку диапазона дат;
- проверку NULL значений;
- проверку дублей;
- проверку KPI;
- проверку идемпотентной загрузки.

## Результат

MART dataset успешно загружается в PostgreSQL и проверяется SQL-запросами.

---

# Текущее состояние проекта

На текущем этапе проект представляет собой полноценный ETL pipeline:

Open-Meteo API
        ↓
RAW JSON
        ↓
Normalized CSV
        ↓
Daily MART
        ↓
PostgreSQL
        ↓
SQL Validation

Пайплайн является воспроизводимым, модульным и готовым к дальнейшей интеграции с BI/dashboard инструментами.

---

# Инкрементальность и идемпотентность

## Full режим

Full режим выполняет полный ETL pipeline:

Extract → Normalize → Mart → Load

При full-запуске:
- создаются новые raw/normalized/mart артефакты;
- витрина PostgreSQL полностью перезаписывается;
- state обновляется после успешного завершения всех этапов.

Повторный full-запуск не создает логических дублей.

---

## Incremental режим

Incremental режим использует сохраненный watermark и state пайплайна.

Для текущего проекта watermark:
- последняя дата mart-таблицы.

Incremental запуск:
- повторно выполняет pipeline;
- безопасно обновляет итоговый результат;
- не создает дубли в PostgreSQL.

---

## State пайплайна

State хранится в:

data/state/state_variant_06.json

State содержит:
- variant_id;
- source_type;
- mode;
- last_watermark;
- business_key;
- last_mart_file;
- last_successful_run.

State обновляется только после успешного завершения всех обязательных этапов пайплайна.

---

## Business Key

Business key витрины:

date + city_id

Эта комбинация делает запись уникальной, потому что:
- одна строка mart соответствует одному дню;
- данные строятся для одного города;
- для одной даты и одного города должна существовать только одна агрегированная запись.

---

## Идемпотентность

Пайплайн является идемпотентным:
- повторный запуск с одинаковыми входными данными не создает логических дублей;
- PostgreSQL таблица перезаписывается через replace strategy;
- state и watermark обновляются безопасно;
- повторный incremental запуск сохраняет стабильный результат.

# Week 6 — Data Quality Framework

## Цель

Реализовать автоматизированные проверки качества данных для аналитической витрины.

## Выполненные задачи

* Реализирован модуль:

src/pipeline/dq.py

* Добавлены проверки:

  * non-empty dataset;
  * not-null business fields;
  * uniqueness business key;
  * temperature range validation;
  * precipitation validation;
  * wind speed validation.

* Формируется отчет:

docs/dq_report.json

## Проверяемые поля

* date
* city_id
* t_mean
* precipitation_sum
* wind_speed_max

## Результат

После каждого запуска pipeline автоматически выполняются DQ проверки и формируется отчет о качестве данных.

---

# Week 7 — Data Visualization

## Цель

Выполнить визуальный анализ погодных данных.

## Выполненные задачи

* Создан notebook:

notebooks/week7_viz.ipynb

* Построены визуализации:

  * временной ряд температуры;
  * распределение температуры;
  * рейтинг погодных показателей;
  * диагностика временных рядов.

* Графики сохранены в:

docs/figures/

## Результат

Получены визуальные артефакты для анализа погодных данных и подготовки BI отчетности.

---

# Week 8 — State Management и Watermark

## Цель

Подготовить пайплайн к инкрементальной обработке данных.

## Выполненные задачи

* Реализовано хранение состояния пайплайна:

data/state/state_variant_06.json

* Добавлены:

  * last_watermark;
  * last_successful_run;
  * business_key;
  * source metadata.

* Реализовано безопасное обновление state после успешного завершения pipeline.

## Результат

Pipeline поддерживает концепцию watermark и готов к incremental processing.

---

# Week 9 — Incremental Processing

## Цель

Реализовать инкрементальную обработку данных.

## Выполненные задачи

* Определен watermark:

date + city_id

* Реализована логика повторного запуска без появления логических дублей.
* Добавлена поддержка incremental режима.
* Реализована безопасная работа со state файлами.

## Результат

Pipeline поддерживает incremental execution и повторные запуски.

---

# Week 10 — Docker и Metabase

## Цель

Контейнеризировать аналитическую платформу и подключить BI слой.

## Выполненные задачи

* Установлен Docker Desktop.
* Создан:

docker-compose.yml

* Поднят PostgreSQL контейнер.
* Поднят Metabase контейнер.
* Настроено хранение данных через Docker Volumes.

Созданные volumes:

* pgdata
* metabase_data

## BI Integration

Metabase подключен к PostgreSQL:

mart_open_meteo

Построены:

* табличные отчеты;
* фильтрация данных;
* визуальный анализ KPI.

## Результат

Проект получил полноценный BI слой через Metabase.

---

# Week 11 — Airflow Orchestration

## Цель

Автоматизировать выполнение ETL pipeline через Apache Airflow.

## Выполненные задачи

* Установлен Apache Airflow 2.9.

* Настроен запуск через Docker Compose.

* Созданы сервисы:

  * airflow-webserver;
  * airflow-scheduler;
  * airflow-db.

* Реализован DAG:

airflow/dags/etl_variant_06.py

## DAG Structure

Pipeline состоит из задач:

extract
↓
transform
↓
load
↓
dq

## Airflow Features

* автоматическое расписание;
* task dependency management;
* retry support;
* execution logs;
* monitoring через Airflow UI.

## Результат

Pipeline полностью оркестрируется через Apache Airflow.

---

# Week 12 — Retry Safety, Backfill и DQ Gate

## Цель

Подготовить Airflow pipeline к безопасным повторным запускам и backfill.

## Выполненные задачи

* Реализован DQ Gate перед загрузкой данных.
* DQ проверки могут останавливать DAG при обнаружении ошибок.
* Обновлен порядок задач:

extract
↓
transform
↓
dq
↓
load

* Добавлена поддержка логического периода выполнения через:

{{ ds }}

* Реализована retry-safe загрузка в PostgreSQL.

## Retry Safety

В load.py используется стратегия:

if_exists="replace"

Это предотвращает появление дублей при повторном запуске задач.

## Backfill Safety

Pipeline поддерживает запуск за прошлые интервалы без нарушения целостности данных.

## Результат

Airflow DAG безопасен для:

* retries;
* manual reruns;
* backfill execution;
* повторной загрузки данных.

---

# Финальная архитектура проекта

Open-Meteo API
↓
Extract
↓
RAW JSON
↓
Normalize
↓
Normalized CSV
↓
Mart
↓
DQ Checks
↓
PostgreSQL
↓
Metabase
↓
Airflow Orchestration

---

# Итог проекта

В рамках проекта реализована полноценная mini Data Platform:

* API ingestion;
* RAW layer;
* NORMALIZED layer;
* MART layer;
* PostgreSQL storage;
* SQL validation;
* Data Quality framework;
* State management;
* Incremental processing;
* Docker infrastructure;
* Metabase BI layer;
* Apache Airflow orchestration;
* Retry-safe и backfill-safe execution.

Проект является воспроизводимым, контейнеризированным и соответствует базовым практикам Data Engineering.
