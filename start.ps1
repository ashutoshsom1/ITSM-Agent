# ITSM AI Agent - Quick Start Script for Windows
# Run this script to set up and start the development server

Write-Host "🤖 ITSM AI Agent - Development Setup" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# Check Python installation
Write-Host "🐍 Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.11 or later." -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (Test-Path "venv") {
    Write-Host "✅ Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Check environment file
if (Test-Path ".env") {
    Write-Host "✅ Environment file found" -ForegroundColor Green
} else {
    if (Test-Path ".env.template") {
        Write-Host "📋 Copying environment template..." -ForegroundColor Yellow
        Copy-Item ".env.template" ".env"
        Write-Host "⚠️  Please edit .env file with your Azure credentials before running the server" -ForegroundColor Yellow
        Write-Host "   Required: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, COSMOS_ENDPOINT, COSMOS_KEY" -ForegroundColor Yellow
        Read-Host "Press Enter when you've configured .env file"
    } else {
        Write-Host "❌ No environment template found" -ForegroundColor Red
        exit 1
    }
}

# Start the server
Write-Host "🚀 Starting development server..." -ForegroundColor Green
Write-Host "📍 Server will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🔍 Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "-" * 50

try {
    python run.py
} catch {
    Write-Host "❌ Error starting server: $_" -ForegroundColor Red
}

Write-Host "👋 Development server stopped" -ForegroundColor Yellow
