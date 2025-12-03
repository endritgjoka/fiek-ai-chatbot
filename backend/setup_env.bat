@echo off
REM Setup script for FIEK AI Chatbot (Windows)
REM This script creates a virtual environment and installs all dependencies

echo ==========================================
echo FIEK AI Chatbot - Environment Setup
echo ==========================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo [OK] Python found
python --version

REM Create virtual environment
echo.
echo Creating virtual environment...
if exist venv (
    echo [WARNING] Virtual environment already exists. Removing old one...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment created

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing Python dependencies...
echo This may take several minutes...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

REM Check for .env file
echo.
if not exist .env (
    echo [WARNING] .env file not found. Creating from .env.example...
    if exist .env.example (
        copy .env.example .env
        echo [OK] Created .env file. Please edit it and add your OPENAI_API_KEY
    ) else (
        echo [WARNING] .env.example not found. Please create .env file manually with OPENAI_API_KEY
    )
) else (
    echo [OK] .env file already exists
)

echo.
echo ==========================================
echo Setup completed successfully!
echo ==========================================
echo.
echo Next steps:
echo 1. Edit backend\.env and add your OPENAI_API_KEY
echo 2. (Optional) Install Tesseract OCR for scanned PDF support:
echo    Download from: https://github.com/UB-Mannheim/tesseract/wiki
echo 3. Run data ingestion: python models\ingest.py
echo 4. Start the app:
echo    - Flask: python app.py
echo    - Streamlit: streamlit run appV2.py
echo.
echo To activate the virtual environment in the future, run:
echo   venv\Scripts\activate
echo.
pause

