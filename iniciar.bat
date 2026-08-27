@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ============================================================
REM PIGAS - MONITORAMENTO
REM ============================================================

set "ROOT=D:\Projeto\PIGAS4364-2025_Monitoramento-main"

title PIGAS - Monitoramento

echo ========================================
echo       PIGAS - MONITORAMENTO
echo ========================================
echo.
echo Projeto: %ROOT%
echo.

REM ============================================================
REM VERIFICAR PROJETO
REM ============================================================

if not exist "%ROOT%\" (
    echo [ERRO] Diretorio do projeto nao encontrado:
    echo %ROOT%
    echo.
    pause
    exit /b 1
)

REM ============================================================
REM VERIFICAR PYTHON USANDO PY
REM ============================================================

echo ========================================
echo Verificando Python...
echo ========================================
echo.

py --version >nul 2>&1

if errorlevel 1 (
    echo.
    echo [ERRO] Python Launcher "py" nao encontrado.
    echo.
    echo Instale o Python pelo site oficial.
    echo Durante a instalacao, marque:
    echo.
    echo     Add python.exe to PATH
    echo.
    echo E certifique-se de instalar o Python Launcher.
    echo.
    pause
    exit /b 1
)

for /f "delims=" %%P in ('py --version 2^>^&1') do (
    echo [OK] %%P
)

echo.

REM ============================================================
REM CAMERA
REM ============================================================

echo ========================================
echo       CAMERA
echo ========================================
echo.

if not exist "%ROOT%\Camera\" (
    echo [ERRO] Pasta Camera nao encontrada:
    echo %ROOT%\Camera
    echo.
    pause
    exit /b 1
)

if not exist "%ROOT%\Camera\programa.py" (
    echo [ERRO] programa.py nao encontrado:
    echo %ROOT%\Camera\programa.py
    echo.
    pause
    exit /b 1
)

if not exist "%ROOT%\Camera\venv\Scripts\activate.bat" (

    echo [CAMERA] Venv nao encontrada.
    echo [CAMERA] Criando venv usando PY...

    py -m venv "%ROOT%\Camera\venv"

    if errorlevel 1 (
        echo.
        echo [ERRO] Falha ao criar venv da Camera.
        pause
        exit /b 1
    )

    echo.
    echo [CAMERA] Venv criada.
    echo.

    echo [CAMERA] Instalando dependencias...

    call "%ROOT%\Camera\venv\Scripts\activate.bat"

    py -m pip install --upgrade pip

    if errorlevel 1 (
        echo.
        echo [ERRO] Falha ao atualizar pip da Camera.
        call "%ROOT%\Camera\venv\Scripts\deactivate.bat" 2>nul
        pause
        exit /b 1
    )

    py -m pip install opencv-python ultralytics torch requests watchdog

    if errorlevel 1 (
        echo.
        echo [ERRO] Falha ao instalar dependencias da Camera.
        call "%ROOT%\Camera\venv\Scripts\deactivate.bat" 2>nul
        pause
        exit /b 1
    )

    call "%ROOT%\Camera\venv\Scripts\deactivate.bat" 2>nul

    echo.
    echo [CAMERA] Dependencias instaladas.

) else (

    echo [CAMERA] Venv encontrada.
)

echo.

REM ============================================================
REM YOLO
REM ============================================================

echo ========================================
echo          YOLO
echo ========================================
echo.

if not exist "%ROOT%\YOLO\" (
    echo [ERRO] Pasta YOLO nao encontrada:
    echo %ROOT%\YOLO
    echo.
    pause
    exit /b 1
)

if not exist "%ROOT%\YOLO\testeC1.py" (
    echo [ERRO] testeC1.py nao encontrado:
    echo %ROOT%\YOLO
    echo.
    pause
    exit /b 1
)

if not exist "%ROOT%\YOLO\venv\Scripts\activate.bat" (

    echo [YOLO] Venv nao encontrada.
    echo [YOLO] Criando venv usando PY...

    py -m venv "%ROOT%\YOLO\venv"

    if errorlevel 1 (
        echo.
        echo [ERRO] Falha ao criar venv do YOLO.
        pause
        exit /b 1
    )

    echo.
    echo [YOLO] Venv criada.
    echo.

    echo [YOLO] Instalando dependencias...

    call "%ROOT%\YOLO\venv\Scripts\activate.bat"

    py -m pip install --upgrade pip

    if errorlevel 1 (
        echo.
        echo [ERRO] Falha ao atualizar pip do YOLO.
        call "%ROOT%\YOLO\venv\Scripts\deactivate.bat" 2>nul
        pause
        exit /b 1
    )

    py -m pip install opencv-python ultralytics torch requests watchdog

    if errorlevel 1 (
        echo.
        echo [ERRO] Falha ao instalar dependencias do YOLO.
        call "%ROOT%\YOLO\venv\Scripts\deactivate.bat" 2>nul
        pause
        exit /b 1
    )

    call "%ROOT%\YOLO\venv\Scripts\deactivate.bat" 2>nul

    echo.
    echo [YOLO] Dependencias instaladas.

) else (

    echo [YOLO] Venv encontrada.
)

echo.

REM ============================================================
REM BACKEND
REM ============================================================

echo ========================================
echo         BACKEND
echo ========================================
echo.

if not exist "%ROOT%\backend\" (
    echo [ERRO] Pasta backend nao encontrada:
    echo %ROOT%\backend
    echo.
    pause
    exit /b 1
)

if not exist "%ROOT%\backend\mvnw.cmd" (
    echo [ERRO] mvnw.cmd nao encontrado:
    echo %ROOT%\backend\mvnw.cmd
    echo.
    pause
    exit /b 1
)

echo [BACKEND] Projeto encontrado.
echo.

REM ============================================================
REM CRIAR SUPERVISOR POWERSHELL
REM ============================================================

echo ========================================
echo Criando supervisor...
echo ========================================
echo.

set "SUPERVISOR=%TEMP%\pigas_supervisor_%RANDOM%_%RANDOM%.ps1"

(
    echo $ErrorActionPreference = "Continue"
    echo.
    echo $root = "%ROOT%"
    echo.
    echo function Start-Camera {
    echo.
    echo     Write-Host "[CAMERA] Iniciando programa.py..." -ForegroundColor Cyan
    echo.
    echo     $work = Join-Path $root "Camera"
    echo     $activate = Join-Path $work "venv\Scripts\activate.bat"
    echo.
    echo     if ^(-not ^(Test-Path $activate^)^) {
    echo         Write-Host "[CAMERA] activate.bat nao encontrado!" -ForegroundColor Red
    echo         return $null
    echo     }
    echo.
    echo     $command = "title PIGAS-Camera && call `"$activate`" && py programa.py"
    echo.
    echo     return Start-Process `
    echo         -FilePath "cmd.exe" `
    echo         -ArgumentList @^("/c", $command^) `
    echo         -WorkingDirectory $work `
    echo         -PassThru
    echo }
    echo.
    echo function Start-YOLO {
    echo.
    echo     Write-Host "[YOLO] Iniciando testeC1.py..." -ForegroundColor Magenta
    echo.
    echo     $work = Join-Path $root "YOLO"
    echo     $activate = Join-Path $work "venv\Scripts\activate.bat"
    echo.
    echo     if ^(-not ^(Test-Path $activate^)^) {
    echo         Write-Host "[YOLO] activate.bat nao encontrado!" -ForegroundColor Red
    echo         return $null
    echo     }
    echo.
    echo     $command = "title PIGAS-YOLO && call `"$activate`" && py testeC1.py"
    echo.
    echo     return Start-Process `
    echo         -FilePath "cmd.exe" `
    echo         -ArgumentList @^("/c", $command^) `
    echo         -WorkingDirectory $work `
    echo         -PassThru
    echo }
    echo.
    echo function Start-Backend {
    echo.
    echo     Write-Host "[BACKEND] Iniciando Spring Boot..." -ForegroundColor Green
    echo.
    echo     $work = Join-Path $root "backend"
    echo     $command = "title PIGAS-Backend && call mvnw.cmd spring-boot:run"
    echo.
    echo     return Start-Process `
    echo         -FilePath "cmd.exe" `
    echo         -ArgumentList @^("/c", $command^) `
    echo         -WorkingDirectory $work `
    echo         -PassThru
    echo }
    echo.
    echo Write-Host "========================================" -ForegroundColor White
    echo Write-Host "       PIGAS - SUPERVISOR" -ForegroundColor White
    echo Write-Host "========================================" -ForegroundColor White
    echo Write-Host ""
    echo.
    echo $camera = Start-Camera
    echo Start-Sleep -Seconds 2
    echo.
    echo $yolo = Start-YOLO
    echo Start-Sleep -Seconds 2
    echo.
    echo $backend = Start-Backend
    echo.
    echo Write-Host ""
    echo Write-Host "[SUPERVISOR] Camera iniciada." -ForegroundColor Cyan
    echo Write-Host "[SUPERVISOR] YOLO iniciado." -ForegroundColor Magenta
    echo Write-Host "[SUPERVISOR] Backend iniciado." -ForegroundColor Green
    echo Write-Host ""
    echo.
    echo while ^($true^) {
    echo.
    echo     Start-Sleep -Seconds 3
    echo.
    echo     # CAMERA
    echo     if ^($null -eq $camera -or $camera.HasExited^) {
    echo.
    echo         Write-Host "[CAMERA] Processo encerrado!" -ForegroundColor Red
    echo         Write-Host "[CAMERA] Reiniciando em 5 segundos..." -ForegroundColor Yellow
    echo.
    echo         Start-Sleep -Seconds 5
    echo         $camera = Start-Camera
    echo.
    echo     }
    echo.
    echo     # YOLO
    echo     if ^($null -eq $yolo -or $yolo.HasExited^) {
    echo.
    echo         Write-Host "[YOLO] Processo encerrado!" -ForegroundColor Red
    echo         Write-Host "[YOLO] Reiniciando em 5 segundos..." -ForegroundColor Yellow
    echo.
    echo         Start-Sleep -Seconds 5
    echo         $yolo = Start-YOLO
    echo.
    echo     }
    echo.
    echo     # BACKEND
    echo     if ^($null -eq $backend -or $backend.HasExited^) {
    echo.
    echo         Write-Host "[BACKEND] Processo encerrado!" -ForegroundColor Red
    echo         Write-Host "[BACKEND] Reiniciando em 5 segundos..." -ForegroundColor Yellow
    echo.
    echo         Start-Sleep -Seconds 5
    echo         $backend = Start-Backend
    echo.
    echo     }
    echo.
    echo }
) > "%SUPERVISOR%"

if not exist "%SUPERVISOR%" (
    echo.
    echo [ERRO] Nao foi possivel criar o supervisor.
    echo.
    pause
    exit /b 1
)

echo [OK] Supervisor criado.
echo.

REM ============================================================
REM INICIAR SUPERVISOR
REM ============================================================

echo ========================================
echo Iniciando processos...
echo ========================================
echo.

start "PIGAS Supervisor" powershell.exe ^
    -NoProfile ^
    -ExecutionPolicy Bypass ^
    -File "%SUPERVISOR%"

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao iniciar supervisor.
    echo.
    pause
    exit /b 1
)

echo [OK] Supervisor iniciado.
echo.

REM ============================================================
REM AGUARDAR BACKEND
REM ============================================================

echo ========================================
echo Aguardando Backend...
echo ========================================
echo.
echo URL: http://localhost:8080
echo.

set /a WAIT_COUNT=0
set /a MAX_WAIT=150

:WAIT_BACKEND

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
    "try { $r = Invoke-WebRequest -Uri 'http://localhost:8080' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } else { exit 1 } } catch { exit 1 }"

if not errorlevel 1 (
    goto BACKEND_OK
)

set /a WAIT_COUNT+=1

if !WAIT_COUNT! GEQ !MAX_WAIT! (
    echo.
    echo [ERRO] Backend nao ficou disponivel apos aproximadamente 5 minutos.
    echo.
    echo Verifique a janela PIGAS-Backend.
    echo.
    goto FINISH_STARTUP
)

echo [AGUARDANDO] Backend ainda nao respondeu...
echo [AGUARDANDO] Tentativa !WAIT_COUNT! de !MAX_WAIT!

timeout /t 2 /nobreak >nul

goto WAIT_BACKEND

REM ============================================================
REM BACKEND OK
REM ============================================================

:BACKEND_OK

echo.
echo ========================================
echo Backend iniciado com sucesso!
echo ========================================
echo.

start "" "http://localhost:8080"

echo [OK] Navegador aberto.
echo.

REM ============================================================
REM STATUS
REM ============================================================

echo ========================================
echo       PIGAS - SISTEMA ATIVO
echo ========================================
echo.
echo [OK] Supervisor
echo [OK] Backend
echo [OK] Camera / programa.py
echo [OK] YOLO / testeC1.py
echo.
echo O supervisor reiniciara automaticamente
echo qualquer processo que seja encerrado.
echo.

REM ============================================================
REM FINALIZAR INICIALIZACAO
REM ============================================================

:FINISH_STARTUP

timeout /t 5 /nobreak >nul

if exist "%~dp0minimizar.bat" (
    call "%~dp0minimizar.bat"
) else (
    echo.
    echo [AVISO] minimizar.bat nao encontrado.
)

echo.
echo ========================================
echo Sistema iniciado.
echo ========================================
echo.
echo Supervisor executando em segundo plano.
echo.

endlocal
exit /b 0