# LLM Usage Log

## Общие правила

LLM использовался как вспомогательный инструмент для объяснения концепций,
поиска ошибок, проверки структуры и подготовки документации. Код, команды,
данные и артефакты проверялись локальными запусками.

LLM не считается источником фактов или чисел. Метрики рассчитываются кодом, а
ответы LLM принимаются только после проверки.

---

## Week 1 — Окружение и репозиторий

- цель: проверить структуру проекта и сценарий настройки Conda;
- контекст: `broken_env.py`, `requirements.txt`, `scripts/setup_env.bat`;
- применение: объяснение различий между `pip` и `python -m pip`, проверка
  идемпотентности setup-скрипта;
- проверка: `setup_env.bat` завершился с `[OK]`;
- итог: PASS.

## Week 2 — HTTP и RAW

- цель: проверить безопасную работу с HTTP и сохранение RAW;
- контекст: `broken_requests.py`, `src/pipeline/extract.py`, YAML-конфиг;
- применение: уточнение timeout, HTTP status, исключений и JSON parsing;
- проверка: отдельно проверены timeout, HTTP 404, не-JSON и успешный API-запрос;
- итог: PASS.

## Week 3 — NORMALIZED

- цель: проверить преобразование RAW JSON в табличный слой;
- контекст: `src/pipeline/normalize.py`, `notebooks/week3_eda.ipynb`;
- применение: объяснение преобразования datetime/numeric и обработки дублей;
- проверка: получен непустой NORMALIZED-файл с ожидаемыми типами и колонками;
- итог: PASS.

## Week 4 — MART и join

- цель: проверить join со справочником и расчет дневных KPI;
- контекст: `broken_merge.py`, `src/pipeline/mart.py`, `reference/cities.csv`;
- применение: проверка кардинальности `many_to_one` и логики агрегаций;
- проверка: число строк не размножается, MART содержит дневные KPI;
- итог: PASS.

## Week 5 — PostgreSQL

- цель: проверить транзакционную и идемпотентную загрузку MART;
- контекст: `broken_commit.py`, `src/pipeline/load.py`, `docs/sql_checks.md`;
- применение: объяснение commit, транзакций и стратегий загрузки;
- проверка: таблица существует, SQL-проверки проходят, повторная загрузка не
  создает дублей;
- итог: PASS.

## Week 6 — Full и incremental pipeline

- цель: проверить единый запуск, state, watermark и повторные запуски;
- контекст: `broken_append.py`, `src/pipeline/pipeline.py`,
  `data/state/state_variant_06.json`;
- применение: проверка full/incremental логики и атомарного обновления state;
- проверка: full пересобирает данные, incremental обрабатывает только новые даты;
- итог: PASS.

## Week 7 — Визуализация

- цель: проверить корректность временной оси и выбор графиков;
- контекст: `broken_dates_plot.py`, `notebooks/week7_viz.ipynb`;
- применение: объяснение сортировки строковых дат и подписей осей;
- проверка: сохранены time series, distribution и ranking графики;
- итог: PASS.

## Week 8 — Data Quality

- цель: проверить DQ-правила, статусы и unit-тесты;
- контекст: `broken_assert.py`, `src/pipeline/dq.py`, `tests/test_dq.py`;
- применение: уточнение различий PASS/WARNING/FAIL и критичности правил;
- проверка: DQ-отчет содержит 7 PASS, тесты ловят искусственные ошибки;
- итог: PASS.

## Week 9 — Data Governance

- цель: синхронизировать контракт, словарь и машинную проверку схем;
- контекст: `docs/Data_Contract.md`, `docs/data_dictionary.md`,
  `src/pipeline/schema_check.py`;
- применение: проверка nullable, единиц, timezone, naming и changelog;
- проверка: NORMALIZED и MART проходят schema validation;
- итог: PASS.

## Week 10 — Docker и BI

- цель: проверить Compose, volumes и подключение Metabase к PostgreSQL;
- контекст: `docker-compose.yml`, `docs/bi/`;
- применение: уточнение различий container/volume, `stop`/`down`/`down -v`;
- проверка: PostgreSQL и Metabase запускаются, dashboard использует таблицу
  `mart_open_meteo`, артефакты сохранены;
- итог: PASS.

## Week 11 — Airflow orchestration

- цель: проверить DAG, расписание и порядок задач;
- контекст: `airflow/dags/*.py`, Airflow logs и screenshots;
- применение: объяснение `start_date`, `schedule`, `catchup` и зависимости задач;
- проверка: DAG импортируется без ошибок, задачи идут в заданном порядке;
- итог: PASS.

## Week 12 — Retry, backfill и DQ gate

- цель: проверить период одного DAG run и безопасность повторов;
- контекст: `airflow/dags/etl_variant_06.py`, `docs/airflow/week12_validation.md`;
- применение: проверка `data_interval_start/end`, retry-safe load и DQ gate;
- проверка: два периода обработаны отдельно, rerun не создает дублей, критичный
  DQ FAIL блокирует load;
- итог: PASS.

## Week 13 — ML и leakage

- цель: проверить постановку прогноза, split, baseline и метрики;
- контекст: `notebooks/week13_ml.ipynb`, `src/analytics/week13_ml.py`;
- применение: проверка отсутствия target leakage и случайного split по времени;
- проверка: target не входит в признаки, split выполняется по времени, модель
  сравнивается с baseline, артефакты сохранены в `docs/ml/`;
- итог: PASS.

## Week 14 — Проверяемая LLM-сводка

- дата: 2026-06-11;
- цель: сформировать интерпретацию уже рассчитанных погодных показателей;
- контекст: только `docs/llm/context.json` с identity набора, агрегатами, DQ
  summary и ограничениями; RAW и приватные данные не передаются;
- промпт: использовать только предоставленные метрики, не придумывать и не
  вычислять числа, причины называть только гипотезами;
- ответ: `docs/llm/summary.md`;
- проверка: `src/analytics/llm_summary.py` сравнивает все числовые токены ответа
  с разрешенными значениями контекста;
- результат проверки: `docs/llm/validation.json`;
- итог: PASS.

## Итог

Каждая примененная рекомендация проверялась кодом, тестом, SQL-запросом,
сохраненным артефактом или локальным запуском. Непроверенные ответы LLM в
проект не включались.
