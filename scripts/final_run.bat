@echo off
setlocal EnableExtensions

cd /d "%~dp0.."
set "ENV_NAME=python_data_project_env"

set "CONDA_BAT="
for /f "delims=" %%I in ('where conda.bat 2^>nul') do (
    if not defined CONDA_BAT set "CONDA_BAT=%%I"
)
if not defined CONDA_BAT if exist "D:\conda\condabin\conda.bat" (
    set "CONDA_BAT=D:\conda\condabin\conda.bat"
)
if not defined CONDA_BAT (
    echo [ERROR] conda.bat was not found. Run scripts\setup_env.bat first.
    exit /b 1
)

docker compose up -d postgres
if errorlevel 1 exit /b 1

set /a "POSTGRES_WAIT=0"
:wait_postgres
docker compose exec -T postgres pg_isready -U student -d analytics >nul 2>nul
if not errorlevel 1 goto postgres_ready
set /a "POSTGRES_WAIT+=1"
if !POSTGRES_WAIT! GEQ 30 (
    echo [ERROR] PostgreSQL did not become ready.
    exit /b 1
)
powershell -NoProfile -Command "Start-Sleep -Seconds 1"
goto wait_postgres

:postgres_ready
call "%CONDA_BAT%" run -n "%ENV_NAME%" python -m src.pipeline.pipeline --config configs/variant_06.yml --mode full
if errorlevel 1 exit /b 1

call "%CONDA_BAT%" run -n "%ENV_NAME%" python -m src.analytics.week13_ml
if errorlevel 1 exit /b 1

call "%CONDA_BAT%" run -n "%ENV_NAME%" python -m src.analytics.llm_summary
if errorlevel 1 exit /b 1

call "%CONDA_BAT%" run -n "%ENV_NAME%" python -m pytest
if errorlevel 1 exit /b 1

echo [OK] Final project run completed.
exit /b 0
