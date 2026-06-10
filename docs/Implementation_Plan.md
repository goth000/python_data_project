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

## Схема данных

```text
Open-Meteo API
        ↓
RAW JSON
        ↓
NORMALIZED CSV
        ↓
DAILY MART CSV
```

- **RAW** хранит исходный ответ API без аналитических преобразований. Этот
  слой позволяет повторно обработать данные и расследовать ошибки без нового
  запроса к источнику.
- **NORMALIZED** содержит развёрнутые почасовые наблюдения с понятными
  колонками, проверенными типами и бизнес-ключом `city_id + ts`.
- **MART** содержит дневные агрегаты и KPI, обогащённые человекочитаемыми
  данными из справочника `reference/cities.csv`.

Слои разделены, потому что каждый из них решает отдельную задачу и может быть
проверен независимо. Если выполнять получение, очистку, join и агрегацию в
одном файле, сложнее воспроизводить результат, находить ошибки и повторно
использовать исходные данные.

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
- читает `last_watermark` из state;
- вычисляет новый период от следующего дня до `api.params.end_date`;
- извлекает и преобразует только новые даты;
- транзакционно заменяет только новый период в PostgreSQL;
- не создает артефакты, если новых дат нет.

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

State обновляется атомарно только после успешного завершения всех обязательных
этапов пайплайна. Путь `last_mart_file` хранится относительно корня проекта.

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
- full-режим полностью заменяет PostgreSQL таблицу;
- incremental-режим удаляет и повторно вставляет только обрабатываемый период;
- state и watermark обновляются безопасно;
- повторный incremental запуск сохраняет стабильный результат.

# Week 8 — Data Quality Framework

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

После построения mart pipeline запускает DQ-проверки до загрузки в PostgreSQL.
Критичный статус FAIL останавливает pipeline, а WARNING сохраняется в отчёте и не блокирует load.
Правила, допустимые диапазоны и критичность читаются из `configs/variant_06.yml`.

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

# Week 6 — State Management и Watermark

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

# Week 9 — Data Governance

## Цель

Зафиксировать единые схемы, типы, nullable, единицы измерения, timezone и правила именования.
Машиночитаемые схемы normalized и mart хранятся в `configs/variant_06.yml`, а
человеко-ориентированные определения — в `docs/Data_Contract.md` и
`docs/data_dictionary.md`.

`src/pipeline/schema_check.py` сверяет реальные CSV с контрактом: обязательные колонки,
порядок, типы и nullable. Отсутствующая колонка, неверный тип или NULL дают FAIL,
лишняя колонка отмечается WARNING.

## Выполненные задачи

* Дополнены схемы normalized и mart обязательными полями: dtype, nullable, unit и description.
* Добавлены версия контракта и changelog с причинами изменений.
* Зафиксированы правила naming, units и timezone.
* Добавлена автоматическая проверка соответствия контракта и реальных CSV.

## Результат

Контракт и код автоматически сверяются для normalized и mart слоёв.

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

Источник BI — таблица `mart_open_meteo` в PostgreSQL, а не CSV-файл.
Внутри Compose-сети Metabase подключается к host `postgres`; `localhost`
используется только для доступа с Windows-хоста.

Проверка persistence выполнена через `docker compose down` и повторный
`docker compose up -d postgres metabase`: таблица и контрольная строка
сохранились в `pgdata`. Команда `down -v` не используется, так как она удаляет
named volumes и данные.

Построены три визуализации:

* Temperature Trend;
* Rainfall Ranking;
* Max Temperature.

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

## Период одного DAG Run

Основной DAG имеет дневное расписание `@daily`. Один DAG Run отвечает за один
дневной data interval. Дата извлечения берется из
`{{ data_interval_start | ds }}`, а `{{ data_interval_end | ds }}` выводится в
лог как исключающая правая граница интервала. Logical date не используется как
"текущее время".

Для одного периода создаются отдельные артефакты:

```text
data/raw/variant_06/raw_{{ data_interval_start | ds }}.json
data/normalized/variant_06/normalized_{{ data_interval_start | ds }}.csv
data/mart/variant_06/mart_{{ data_interval_start | ds }}.csv
```

Open-Meteo принимает включительные `start_date` и `end_date`, поэтому для
дневного DAG Run extract передает дату начала интервала в оба параметра.

## Retry Safety и идемпотентность

Для задач настроены две повторные попытки. Load запускается в режиме
`incremental` и внутри одной транзакции выполняет стратегию:

1. удалить строки загружаемого периода и города;
2. вставить рассчитанные строки периода;
3. обеспечить уникальный индекс по бизнес-ключу `(date, city_id)`.

Если попытка или весь DAG Run повторяется, тот же период заменяется, а не
добавляется второй раз. Уникальный индекс служит дополнительной защитой.
Альтернативный подход — upsert по бизнес-ключу; он удобен для точечных
изменений, но сложнее простой замены небольшого дневного периода.

## DQ Gate

Порядок задач:

```text
extract -> transform -> dq -> load
```

Критический DQ FAIL завершает `dq.py` ненулевым кодом. Airflow помечает задачу
и DAG Run как failed, поэтому load не запускается и плохие данные не попадают в
PostgreSQL.

## Backfill

При `catchup=True` Airflow может создать отдельный DAG Run для каждого
пропущенного интервала между `start_date` и текущим временем. Без
идемпотентности это могло бы создать дубли. Здесь каждый run обрабатывает свой
день, использует отдельные файлы и заменяет только свой период, поэтому
повторный запуск и backfill безопасны.

В рабочем DAG задано `catchup=False`, чтобы случайно не запускать большой
backfill автоматически. Исторические интервалы можно запускать явно.

## Логи и проверка

Логи содержат data interval, фактический период API, количество извлеченных,
нормализованных, проверенных и загруженных строк, путь файла и режим загрузки.
Отсутствие дублей проверяется SQL-запросом по `(date, city_id)`.

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
