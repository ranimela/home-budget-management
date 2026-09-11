@echo off
title Home Budget Manager Server
echo ============================================================
echo  Starting Home Budget Manager Local Server...
echo ============================================================
echo.

rem Start server launcher (automatically initializes DB, scans inputs & opens 1 browser tab)
uv run python -m app.launcher

