@echo off
cd /d "%~dp0"
:: Agora o próprio Python gerencia o log internamente
uv run main.py
exit