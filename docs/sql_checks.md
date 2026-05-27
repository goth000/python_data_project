# SQL-проверки

Таблица в PostgreSQL: `mart_open_meteo`

## 1. Проверка существования таблицы

SQL:

    \dt

Ожидаемый результат:
- таблица `mart_open_meteo` существует.

---

## 2. Проверка, что таблица не пустая

SQL:

    SELECT COUNT(*) FROM mart_open_meteo;

Ожидаемый результат:
- количество строк больше 0;
- для текущей витрины ожидается 7 строк.

---

## 3. Проверка диапазона дат

SQL:

    SELECT MIN(date), MAX(date)
    FROM mart_open_meteo;

Ожидаемый результат:
- запрос возвращает минимальную и максимальную дату из витрины;
- ожидаемый диапазон: с 2024-05-01 по 2024-05-07.

---

## 4. Проверка NULL в ключевых колонках

SQL:

    SELECT *
    FROM mart_open_meteo
    WHERE date IS NULL
       OR city_id IS NULL;

Ожидаемый результат:
- 0 строк;
- ключевые поля `date` и `city_id` не должны содержать NULL.

---

## 5. Проверка дублей по бизнес-ключу

SQL:

    SELECT date, city_id, COUNT(*) AS row_count
    FROM mart_open_meteo
    GROUP BY date, city_id
    HAVING COUNT(*) > 1;

Ожидаемый результат:
- 0 строк;
- для каждой пары `date + city_id` должна существовать только одна строка.

---

## 6. Проверка KPI

SQL:

    SELECT
        AVG(t_mean) AS avg_temperature,
        MAX(t_max) AS max_temperature,
        SUM(precipitation_sum) AS total_precipitation,
        SUM(rainy_hours) AS total_rainy_hours,
        MAX(wind_speed_max) AS max_wind_speed
    FROM mart_open_meteo;

Ожидаемый результат:
- запрос успешно возвращает агрегированные KPI;
- значения метрик не пустые.

---

## 7. Проверка отрицательных осадков

SQL:

    SELECT *
    FROM mart_open_meteo
    WHERE precipitation_sum < 0;

Ожидаемый результат:
- 0 строк;
- количество осадков не может быть отрицательным.

---

## 8. Проверка идемпотентной загрузки

В `src/pipeline/load.py` используется:

    if_exists="replace"

Ожидаемый результат:
- повторный запуск `load.py` не создает дубли;
- таблица перезаписывается корректно;
- количество строк остается стабильным.