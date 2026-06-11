# Implementation Plan

## Цель проекта

Построить воспроизводимый mini data platform для исторических погодных данных
Open-Meteo по Токио:

```text
API -> RAW -> NORMALIZED -> MART -> DQ -> PostgreSQL -> BI
                                      |
                                      +-> ML -> проверяемая LLM-сводка
```

Вариант проекта: `06`. Бизнес-ключ MART: `date + city_id`.

---

## Week 1 — Окружение и структура

- подготовить папки проекта и GitHub-репозиторий;
- описать зависимости в `requirements.txt`;
- реализовать идемпотентный `scripts/setup_env.bat`;
- добавить `broken_env.py` и базовые документы.

Результат: окружение создается и проверяется одной командой.

## Week 2 — Extract и RAW

- описать API в `configs/variant_06.yml`;
- реализовать timeout, HTTP/JSON checks и обработку ошибок;
- сохранять исходный ответ без преобразований в `data/raw/variant_06/`;
- добавить диагностику `broken_requests.py`.

Результат: воспроизводимый RAW-снимок Open-Meteo.

## Week 3 — NORMALIZED

- преобразовать hourly JSON в DataFrame;
- привести datetime и numeric типы;
- проверить пропуски и удалить дубли по `city_id + ts`;
- сохранить CSV и EDA notebook.

Результат: типизированный почасовой NORMALIZED-слой.

## Week 4 — MART

- проверить уникальность справочника `reference/cities.csv`;
- выполнить `many_to_one` join по `city_id`;
- агрегировать данные до одного города-дня;
- рассчитать `t_mean`, `t_max`, `precipitation_sum`, `rainy_hours`,
  `wind_speed_max`.

Результат: дневная аналитическая витрина.

## Week 5 — PostgreSQL

- поднять PostgreSQL;
- реализовать отдельный `load.py` с транзакцией;
- загрузить MART в `mart_open_meteo`;
- добавить минимум пять SQL-проверок и диагностику commit.

Результат: идемпотентная загрузка и проверяемая таблица.

## Week 6 — Pipeline и incremental

- объединить стадии в CLI `src.pipeline.pipeline`;
- поддержать `full` и `incremental`;
- хранить state и watermark;
- обновлять state только после успешного завершения обязательных стадий.

Результат: единая команда и безопасная обработка новых периодов.

## Week 7 — Визуальный анализ

- построить временной ряд, распределение и ranking;
- корректно преобразовать и отсортировать даты;
- подписать оси и сформулировать выводы;
- сохранить PNG в `docs/figures/`.

Результат: воспроизводимый notebook визуального анализа.

## Week 8 — Data Quality

- вынести DQ в отдельный модуль;
- читать правила и criticality из YAML;
- формировать `docs/dq_report.json`;
- добавить unit-тесты и блокировку load при критичном FAIL.

Результат: автоматический DQ gate.

## Week 9 — Data Governance

- зафиксировать схемы, nullable, единицы, семантику и timezone;
- создать data dictionary и changelog;
- реализовать `schema_check.py`;
- проверить преобразование единиц через `broken_units.py`.

Результат: контракт автоматически сверяется с NORMALIZED и MART.

## Week 10 — Docker и BI

- описать PostgreSQL и Metabase в Docker Compose;
- подключить named volumes;
- подключить Metabase к `mart_open_meteo`;
- создать dashboard из трех визуализаций и сохранить подтверждения.

Результат: воспроизводимый BI-стенд с сохраняемыми данными.

## Week 11 — Airflow

- добавить Airflow services и DAG;
- оркестрировать extract, transform, load и DQ;
- настроить расписание, retries, зависимости и логи;
- документировать `start_date`, `schedule` и `catchup`.

Результат: pipeline запускается и наблюдается через Airflow.

## Week 12 — Period-aware и retry-safe Airflow

- обрабатывать `data_interval_start/end`, а не текущее время;
- создавать отдельные артефакты для каждого периода;
- выполнять DQ до load;
- заменять повторно загружаемый период транзакционно;
- подтвердить безопасность retry, rerun и backfill.

Результат: `extract -> transform -> dq -> load`, без дублей при повторах.

## Week 13 — ML

- прогнозировать температуру следующего часа;
- исключить target leakage;
- выполнить time-based split;
- сравнить Linear Regression с DummyRegressor;
- сохранить метрики, predictions и графики.

Результат: честная оценка простой модели и ее ограничений.

## Week 14 — Финал и LLM

- добавить отдельный LLM report step после вычислений;
- передавать только ограниченный контекст с рассчитанными метриками;
- автоматически отклонять сводку с неизвестными числами;
- вести LLM usage log;
- предоставить финальный сценарий запуска и тег `v1.0-final`.

Результат: воспроизводимый mini-product с DQ, BI, ML и проверяемой сводкой.

---

## Финальная проверка

```cmd
scripts\setup_env.bat
scripts\final_run.bat
```

Ожидаемый результат:

- pipeline завершается успешно;
- PostgreSQL содержит уникальные строки MART;
- DQ не содержит критичных FAIL;
- ML и LLM-артефакты формируются;
- тесты проходят.
