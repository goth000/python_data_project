# Python Data Project

## Week 1

Проект содержит базовую структуру репозитория и автоматическую настройку окружения через Conda.

## Запуск на Windows

Открыть Anaconda Prompt в корне проекта и выполнить:

```cmd
scripts\setup_env.bat
```

## Smoke test

Скрипт `setup_env.bat` автоматически запускает:

```cmd
conda run -n python_data_project_env python broken_env.py
```

Ожидаемый результат:

```text
python: D:\conda\envs\python_data_project_env\python.exe
pandas: 3.0.3
[OK] Environment is ready.
```

## Почему pip install может ставить не туда

На Windows может быть несколько Python-интерпретаторов. Команда `pip install` может относиться к одному Python, а запуск `python script.py` — к другому. Надёжнее использовать `python -m pip install ...` внутри нужного окружения.

## Data Layers

Проект использует многослойную структуру данных:

- raw — исходные ответы API;
- normalized — очищенные табличные данные;
- mart — агрегированная аналитическая витрина.

Pipeline:
API → RAW → NORMALIZED → MART
