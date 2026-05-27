# Data Dictionary

## Общая информация

Словарь данных описывает бизнес-смысл колонок аналитической витрины `mart_open_meteo`.

Гранулярность витрины:

```text
1 row = 1 city-day aggregate
```

Timezone:

```text
Asia/Tokyo
```

---

# Mart Columns

| Column | Business Meaning | Unit | Example / Notes |
|---|---|---|---|
| date | Дата агрегации погодных метрик | YYYY-MM-DD | 2024-05-01 |
| city_id | Уникальный идентификатор города | string | JP_TYO |
| city_name | Название города | string | Tokyo |
| country_code | Код страны | ISO country code | JP |
| timezone | Временная зона наблюдений | TZ database name | Asia/Tokyo |
| t_mean | Средняя температура за день | °C | 17.1 |
| t_max | Максимальная температура за день | °C | 26.5 |
| precipitation_sum | Суммарное количество осадков за день | mm | 37.3 |
| rainy_hours | Количество часов с осадками | hours | 18 |
| wind_speed_max | Максимальная скорость ветра за день | km/h | 50.0 |

---

# KPI Definitions

## t_mean

Средняя температура за сутки.

Рассчитывается как:

```text
AVG(hourly temperature)
```

---

## t_max

Максимальная температура за сутки.

Рассчитывается как:

```text
MAX(hourly temperature)
```

---

## precipitation_sum

Суммарное количество осадков за сутки.

Рассчитывается как:

```text
SUM(hourly precipitation)
```

---

## rainy_hours

Количество часов, в которых precipitation > 0.

---

## wind_speed_max

Максимальная скорость ветра за сутки.

Рассчитывается как:

```text
MAX(hourly wind speed)
```

---

# Interpretation Notes

- Температура хранится в градусах Цельсия.
- Осадки измеряются в миллиметрах.
- Скорость ветра хранится в km/h.
- Все временные данные относятся к timezone Asia/Tokyo.

---

# Business Key

Business key витрины:

```text
date + city_id
```

Каждая строка представляет один день погодных метрик для одного города.