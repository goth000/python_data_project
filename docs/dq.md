# Data Quality Rules

## Общая информация

В проекте реализованы автоматические проверки качества данных (Data Quality checks) для аналитической витрины `mart`.

Проверки выполняются скриптом:

```text
src/pipeline/dq.py
```

Результат проверок сохраняется в:

```text
docs/dq_report.json
```

---

# Слой данных

DQ-проверки выполняются для слоя:

```text
mart
```

Причина:
mart является финальным аналитическим слоем, который используется для BI, SQL и визуализаций.

---

# Business Key

Business key витрины:

```text
date + city_id
```

Каждая комбинация даты и города должна быть уникальной.

---

# DQ Rules

| Rule | Severity | Description |
|---|---|---|
| non_empty | critical | Витрина не должна быть пустой |
| not_null_date | critical | Поле `date` не должно содержать NULL |
| not_null_city_id | critical | Поле `city_id` не должно содержать NULL |
| unique_business_key | critical | Не должно быть дублей по `date + city_id` |
| temperature_range | warning | Средняя температура должна быть в диапазоне [-100, 100] |
| non_negative_precipitation | critical | Осадки не могут быть отрицательными |
| non_negative_wind | warning | Скорость ветра не может быть отрицательной |

---

# Статусы проверок

| Status | Meaning |
|---|---|
| PASS | Проверка успешно пройдена |
| FAIL | Обнаружена ошибка качества данных |
| WARNING | Обнаружено потенциально подозрительное значение |

---

# Unit Tests

Unit tests находятся в:

```text
tests/test_dq.py
```

Тестируются:

- positive cases;
- negative cases;
- boundary cases.

---

# Диагностический пример

Файл:

```text
broken_assert.py
```

показывает распространенную ошибку:

```python
df["x"].notna
```

без вызова метода:

```python
df["x"].notna().all()
```

что приводит к ложному прохождению проверки.