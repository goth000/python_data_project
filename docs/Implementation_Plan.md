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