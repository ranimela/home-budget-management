@echo off
title Home Budget Manager Server
echo ============================================================
echo  Starting Home Budget Manager Local Development Server...
echo ============================================================
echo.

rem Start server in background using uv python launcher
start "" /B uv run python -m app.launcher

echo Waiting for server to initialize...
timeout /t 3 /nobreak >nul

rem Open default web browser
start http://127.0.0.1:8000

echo.
echo ============================================================
echo  Server is active at: http://127.0.0.1:8000
echo ============================================================
