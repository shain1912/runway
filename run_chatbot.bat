@echo off
title Runway Agentic RAG Chatbot Launcher
color 0e

echo ========================================================
echo   Runway Docs Agentic RAG Chatbot Launcher
echo ========================================================
echo.

:: 1. Verify Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [Error] Python is not installed or not in PATH!
    echo Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

:: 2. Setup Virtual Environment
if not exist ".venv" (
    echo [.venv] Creating isolated Python Virtual Environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [Error] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [Success] Virtual environment created.
)

:: Activate Virtual Environment
call .venv\Scripts\activate.bat

:: 3. Install Dependencies
echo [Dependencies] Installing / Upgrading required libraries (anthropic, streamlit, qdrant-client)...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [Error] Failed to install dependencies!
    pause
    exit /b 1
)
echo [Success] Dependencies verified and installed.
echo.

:: 4. API Key Configuration Info
echo ========================================================
echo   API Key Configuration
echo ========================================================
echo [Info] API Keys will be loaded directly from your .env file.
echo [Info] Streamlit will let you select between MINIMAX1, MINIMAX2, MINIMAX3, MINIMAX4, etc.
echo.

:menu
echo ========================================================
echo   Select Action to Perform:
echo ========================================================
echo   [1] Ingest Documents (Run ingest_qdrant.py)
echo   [2] Start Streamlit Agentic Chatbot (Run rag_app.py)
echo   [3] Both (Ingest first, then Start Chatbot)
echo   [4] Setup and Start Qdrant Server (Windows Standalone)
echo   [5] Exit
echo ========================================================
set /p choice="Enter choice [1-5]: "

if "%choice%"=="1" goto ingest
if "%choice%"=="2" goto app
if "%choice%"=="3" goto both
if "%choice%"=="4" goto qdrant
if "%choice%"=="5" goto exit

echo [Error] Invalid choice! Please select 1, 2, 3, 4, or 5.
echo.
goto menu

:ingest
echo.
echo ========================================================
echo   Running Ingestion Pipeline...
echo ========================================================
echo [Note] Make sure Qdrant is running at localhost:6333
echo.
python ingest_qdrant.py
echo.
echo Ingestion task finished.
pause
goto menu

:app
echo.
echo ========================================================
echo   Starting Streamlit Agentic Chatbot Web Application...
echo ========================================================
echo.
streamlit run rag_app.py
pause
goto menu

:both
echo.
echo ========================================================
echo   1. Running Ingestion...
echo ========================================================
python ingest_qdrant.py
echo.
echo ========================================================
echo   2. Starting Streamlit Web App...
echo ========================================================
echo.
streamlit run rag_app.py
pause
goto menu

:qdrant
echo.
echo ========================================================
echo   Setting up / Launching Local Qdrant Server
echo ========================================================
echo [Info] Checking if Qdrant is already running on port 6333...
:: NOTE: Hybrid search (dense + BM25 sparse with RRF fusion) needs Qdrant >= 1.10 (Query API).
:: To upgrade an existing install, delete the 'qdrant' folder so the new binary is downloaded.
:: If the version below 404s, change it to any released tag >= 1.10 (see github.com/qdrant/qdrant/releases).
powershell -Command "if (Test-NetConnection -ComputerName localhost -Port 6333 -WarningAction SilentlyContinue | Where-Object {$_.TcpTestSucceeded -eq $true}) { Write-Host 'Qdrant is already running on port 6333!' } else { if (-not (Test-Path 'qdrant')) { New-Item -ItemType Directory -Path 'qdrant' | Out-Null; Write-Host 'Downloading Qdrant Windows binary v1.12.4...'; Invoke-WebRequest -Uri 'https://github.com/qdrant/qdrant/releases/download/v1.12.4/qdrant-x86_64-pc-windows-msvc.zip' -OutFile 'qdrant\qdrant.zip'; Write-Host 'Extracting Qdrant...'; Expand-Archive -Path 'qdrant\qdrant.zip' -DestinationPath 'qdrant' -Force; Remove-Item 'qdrant\qdrant.zip' }; Write-Host 'Starting Qdrant Server in a background window...'; Start-Process -FilePath 'qdrant\qdrant.exe' -WorkingDirectory 'qdrant' -WindowStyle Normal }"
echo.
echo Please wait 5 seconds for Qdrant to boot...
timeout /t 5 /nobreak >nul
goto menu

:exit
echo.
echo Thank you for practicing Agentic RAG!
echo.
pause
exit /b 0
