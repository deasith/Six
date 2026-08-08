@echo off
REM ============================================================
REM  Lanzador de JARVIS para Windows.
REM  Haz doble clic en este archivo para abrir tu asistente.
REM ============================================================
title JARVIS

REM Intenta con "python"; si no, prueba con "py".
where python >nul 2>nul
if %errorlevel%==0 (
    python "%~dp0jarvis.py"
    goto :fin
)

where py >nul 2>nul
if %errorlevel%==0 (
    py "%~dp0jarvis.py"
    goto :fin
)

echo.
echo  No encuentro Python en tu equipo.
echo  Descargalo gratis en: https://www.python.org/downloads/
echo  IMPORTANTE: al instalar, marca la casilla "Add Python to PATH".
echo.
pause

:fin
