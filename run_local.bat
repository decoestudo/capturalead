@echo off
:: Roda o app localmente usando seu IP residencial (sem Docker)
:: PostgreSQL e Redis continuam no Docker nas portas 5433 e 6379

set DATABASE_URL=postgresql://leads_user:leads_pass@localhost:5433/leads_db
set REDIS_URL=redis://localhost:6379

:: Carrega o restante das variaveis do .env
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if not "%%A"=="" if not "%%A:~0,1%"=="#" (
        if "%%A" NEQ "DATABASE_URL" if "%%A" NEQ "REDIS_URL" (
            set %%A=%%B
        )
    )
)

echo Iniciando app local com IP residencial...
echo DATABASE_URL=%DATABASE_URL%
echo REDIS_URL=%REDIS_URL%
echo.

py main.py
