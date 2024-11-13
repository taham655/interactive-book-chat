@echo off
REM reset_migrations.bat

REM Load environment variables if .env exists
if exist .env (
    for /f "tokens=*" %%a in (.env) do set %%a
)

REM Set default values if not in environment
if "%DB_NAME%"=="" set DB_NAME=fabled
if "%DB_USER%"=="" set DB_USER=postgres
if "%DB_PASSWORD%"=="" set DB_PASSWORD=tahatalib85

echo Resetting migration state...
psql -U %DB_USER% -d %DB_NAME% -c "DROP TABLE IF EXISTS alembic_version;"

echo Removing existing migrations...
if exist migrations\ (
    rmdir /s /q migrations
)

REM Create database if it doesn't exist
psql -U %DB_USER% -c "DROP DATABASE IF EXISTS %DB_NAME%;"
psql -U %DB_USER% -c "CREATE DATABASE %DB_NAME%;"

echo Initializing fresh migrations...
set FLASK_APP=app.py
flask db init

echo Creating initial migration...
flask db migrate -m "Initial migration"

echo Applying migration...
flask db upgrade

echo Migration reset complete!