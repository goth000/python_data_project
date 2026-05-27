# Python Data Project

## Описание проекта

Проект реализует учебный ETL pipeline для обработки погодных данных Open-Meteo.

Pipeline включает:

1. Extract — получение сырых JSON данных из API;
2. Normalize — очистка и нормализация данных;
3. Mart — построение аналитической витрины;
4. Load — загрузка витрины в PostgreSQL;
5. Visualization — визуальный анализ данных и построение графиков.

---

# Структура проекта

```text
configs/           - YAML конфигурации
data/raw/          - сырые JSON данные
data/normalized/   - нормализованные CSV
data/mart/         - аналитические витрины
data/state/        - state / watermark файлы

docs/              - документация проекта
docs/figures/      - PNG графики и визуализации

notebooks/         - Jupyter / Colab notebooks

reference/         - reference tables

scripts/           - setup scripts

src/pipeline/      - ETL pipeline

tests/             - diagnostic scripts
```

---

# Используемый стек

- Python
- Pandas
- PostgreSQL
- SQLAlchemy
- Matplotlib
- Docker
- Conda

---

# Настройка окружения

## Windows + Conda

Открыть Anaconda Prompt в корне проекта и выполнить:

```cmd
scripts\setup_env.bat
```

---

# Smoke Test

Скрипт `setup_env.bat` автоматически проверяет окружение.

Ожидаемый результат:

```text
[OK] Environment is ready.
```

---

# Data Layers

Проект использует многослойную структуру хранения данных.

## RAW

Сырые JSON ответы API:

```text
data/raw/
```

## NORMALIZED

Очищенные табличные данные:

```text
data/normalized/
```

## MART

Агрегированная аналитическая витрина:

```text
data/mart/
```

Pipeline:

```text
API → RAW → NORMALIZED → MART → POSTGRES
```

---

# ETL Pipeline

Основные pipeline scripts:

```text
src/pipeline/extract.py
src/pipeline/normalize.py
src/pipeline/mart.py
src/pipeline/load.py
src/pipeline/pipeline.py
```

Полный запуск pipeline:

```cmd
conda run -n python_data_project_env python src/pipeline/pipeline.py
```

---

# PostgreSQL

Проект использует PostgreSQL в Docker контейнере.

Пример запуска:

```cmd
docker run --name postgres-course ^
-e POSTGRES_PASSWORD=postgres ^
-e POSTGRES_USER=postgres ^
-e POSTGRES_DB=analytics ^
-p 5432:5432 ^
-d postgres:16
```

---

# SQL Checks

SQL проверки находятся в:

```text
docs/sql_checks.md
```

---

# Visualization

Визуальный анализ выполнен в notebook:

```text
notebooks/week7_viz.ipynb
```

Сгенерированные графики:

```text
docs/figures/
```

---

# Диагностические задания

Проект содержит diagnostic scripts:

```text
broken_env.py
broken_merge.py
broken_requests.py
broken_pandas_read.py
broken_append.py
broken_dates_plot.py
```

---

# Week7 Visualizations

Проект содержит:

- time series plot;
- histogram;
- ranking bar chart;
- datetime sorting diagnostics.