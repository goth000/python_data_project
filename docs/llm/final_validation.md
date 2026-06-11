# Week 14 Final Validation

The complete project was executed with one command:

```cmd
scripts\final_run.bat
```

Validated stages:

```text
Open-Meteo extract: HTTP 200, 168 hourly rows
Normalize: 168 rows
MART: 7 daily rows
DQ: PASS=7, WARNING=0, FAIL=0
PostgreSQL load: 7 rows
ML artifacts: generated
LLM context and summary: generated
LLM numeric validation: PASS
Pytest: 13 passed
```

The default LLM mode is offline and requires no API key. Optional online mode
uses environment variables only and its response must pass the same numeric
validation before it can be saved.
