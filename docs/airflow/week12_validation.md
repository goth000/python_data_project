# Week 12 Validation

## Period-aware runs

The DAG was tested for two different daily intervals:

| Logical date used for test | Data interval | API period | MART rows | Result |
|---|---|---|---:|---|
| 2024-05-02 | 2024-05-01 -> 2024-05-02 | 2024-05-01 | 1 | success |
| 2024-05-03 | 2024-05-02 -> 2024-05-03 | 2024-05-02 | 1 | success |

Each run created period-specific RAW, normalized, and MART files.

## Retry and rerun safety

The interval for 2024-05-01 was run again. Before and after the rerun,
PostgreSQL contained `8 rows / 8 unique business keys`. Load reported:

```text
load period: 2024-05-01 -> 2024-05-01
rows deleted before insert: 1
rows loaded: 1
load mode: incremental
```

This confirms that the period is replaced rather than duplicated. The table
also has a unique index on `(date, city_id)`.

After removing the separate diagnostic row for 2024-04-30, the project table
returned to its expected state:

```text
rows: 7
unique business keys: 7
range: 2024-05-01 -> 2024-05-07
duplicates: 0
```

## DQ gate

The DAG dependency is:

```text
extract -> transform -> dq -> load
```

`dq.py` exits with a non-zero status when a critical rule returns FAIL.
The automated integration test `test_critical_dq_fail_exits_before_load`
verifies this behavior. With Airflow's default `all_success` trigger rule,
load is not executed after a failed DQ task.

## Automated checks

```text
pytest: 7 passed
Airflow import errors: none
```
