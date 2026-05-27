# Data Contract

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

| column | type | description |
|---|---|---|
| ts | datetime | время наблюдения |
| temperature_2m | float | температура на 2м |
| relative_humidity_2m | float | относительная влажность |
| precipitation | float | количество осадков |
| wind_speed_10m | float | скорость ветра |
| city_id | string | идентификатор города |

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

| column | description |
|---|---|
| date | дата агрегации |
| city_id | идентификатор города |
| city_name | название города |
| country_code | код страны |
| timezone | временная зона |
| t_mean | средняя температура за день |
| t_max | максимальная температура за день |
| precipitation_sum | сумма осадков за день |
| rainy_hours | количество дождливых часов |
| wind_speed_max | максимальная скорость ветра |

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
- проверку идемпотентной загрузки.