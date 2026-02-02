@echo off
echo ====================================
echo  Self-Correcting RAG System
echo ====================================
echo.
echo Checking environment setup...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist "backend\.env" (
    echo WARNING: .env file not found
    echo Copy backend\.env.example to backend\.env and configure your API keys
    echo.
    echo For OpenAI: Set OPENAI_API_KEY=your_key_here
    echo For Ollama: Install Ollama and run: ollama pull mistral && ollama pull nomic-embed-text
    echo.
)

echo Starting the RAG System...
echo.
echo Server will be available at: http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

cd backend
python app.py

echo.
echo Server stopped.
pause
