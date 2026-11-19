@echo off
REM ============================================================================
REM  Abrir Interface Web - GBP Lead Finder
REM  Duplo clique neste arquivo para abrir a interface no navegador.
REM
REM  Este arquivo deve ficar na mesma pasta do main.py e do server.py
REM  (a pasta do projeto gbp_lead_finder). Ele usa o caminho de onde esta
REM  salvo, entao pode ser movido junto com o projeto sem precisar editar
REM  nada.
REM ============================================================================

title GBP Lead Finder - Interface Web
cd /d "%~dp0"

if not exist "server.py" (
    echo.
    echo [ERRO] Nao foi possivel encontrar server.py nesta pasta.
    echo Verifique se este arquivo .bat esta na pasta do projeto
    echo gbp_lead_finder, junto com main.py e server.py.
    echo.
    pause
    exit /b 1
)

python server.py

echo.
echo O servidor foi encerrado.
pause
