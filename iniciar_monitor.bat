@echo off
cd /d "%~dp0"

:: Escreve a data e hora atual no arquivo de log
echo ============= [%date% %time%] Iniciando varredura... >> monitor_logs.txt

:: O comando ">>" joga tudo que apareceria na tela para dentro do arquivo de texto
:: O "2>&1" garante que até os logs de erro crítico do Python sejam salvos lá
uv run glpi_monitor.py >> monitor_logs.txt 2>&1
echo ============= [%date% %time%] Finalizando varredura... >> monitor_logs.txt
echo

exit