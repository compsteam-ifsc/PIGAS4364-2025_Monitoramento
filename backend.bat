@echo off
setlocal EnableExtensions

REM ============================================================
REM PIGAS - BACKEND
REM ============================================================

set "ROOT=D:\Projeto\PIGAS4364-2025_Monitoramento-main"

title PIGAS - Backend

echo ========================================
echo       PIGAS - BACKEND
echo ========================================
echo.
echo Projeto: %ROOT%
echo.

REM Verificar projeto
if not exist "%ROOT%\backend\" (
    echo [ERRO] Pasta backend nao encontrada:
    echo %ROOT%\backend
    pause
    exit /b 1
)

REM Verificar Maven Wrapper
if not exist "%ROOT%\backend\mvnw.cmd" (
    echo [ERRO] mvnw.cmd nao encontrado.
    echo %ROOT%\backend\mvnw.cmd
    pause
    exit /b 1
)

echo [BACKEND] Iniciando...
echo.

cd /d "%ROOT%\backend"

call mvnw.cmd spring-boot:run

echo.
echo [BACKEND] O processo foi encerrado.
pause