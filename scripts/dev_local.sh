#!/bin/bash

# Development script for local development
set -e

echo "🚀 Starting Persona Wizard development environment..."

# Check if we're in the right directory
if [ ! -f "Makefile" ]; then
    echo "❌ Please run this script from the persona-wizard root directory"
    exit 1
fi

# Check dependencies
echo "📋 Checking dependencies..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install
cd ..

# Run setup
echo "⚙️ Running setup..."
make setup

echo "✅ Setup complete!"
echo ""
echo "🎯 To start development:"
echo "   make dev"
echo ""
echo "🧪 To run tests:"
echo "   make test"
echo ""
echo "🐳 To use Docker:"
echo "   docker-compose up"
