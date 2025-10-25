@echo off
echo Starting Local Image Service...
echo.

REM Check if .env file exists
if not exist .env (
    echo Warning: .env file not found!
    echo Please copy .env.example to .env and configure your settings.
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment should be activated
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Install requirements if needed
python -c "import fastapi" 2>nul || (
    echo Installing requirements...
    pip install -r requirements.txt
)

REM Create storage directory
if not exist storage mkdir storage
if not exist storage\images mkdir storage\images

echo.
echo Starting server at http://localhost:8003
echo API Documentation: http://localhost:8003/docs
echo.

REM Start the service
python main.py

pause