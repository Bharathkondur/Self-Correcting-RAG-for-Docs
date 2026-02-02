#!/bin/bash
# Startup script for Unix-based systems (Linux/macOS)

echo "===================================="
echo " Self-Correcting RAG System"
echo "===================================="
echo

echo "Checking environment setup..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "WARNING: .env file not found"
    echo "Copy backend/.env.example to backend/.env and configure your API keys"
    echo
    echo "For OpenAI: Set OPENAI_API_KEY=your_key_here"
    echo "For Ollama: Install Ollama and run: ollama pull mistral && ollama pull nomic-embed-text"
    echo
fi

# Check if requirements are installed
echo "Checking Python dependencies..."
cd backend

if ! python3 -c "import fastapi" &> /dev/null; then
    echo "Installing Python dependencies..."
    python3 -m pip install -r requirements.txt
fi

echo "Starting the RAG System..."
echo
echo "Server will be available at: http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo

python3 app.py