#!/bin/bash

# Persona Wizard Setup Script
# This script sets up the Persona Wizard environment for development and deployment

set -e  # Exit on any error

echo "🚀 Setting up Persona Wizard..."

# Check if Python 3.11+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ $(echo "$PYTHON_VERSION < 3.11" | bc -l) -eq 1 ]]; then
    echo "❌ Python 3.11+ is required. Current version: $PYTHON_VERSION"
    echo "Please install Python 3.11+ using Homebrew: brew install python@3.11"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Install Foundry Local (if available)
echo "🔧 Installing Foundry Local..."
if command -v brew &> /dev/null; then
    if ! command -v foundry &> /dev/null; then
        echo "Installing Foundry Local via Homebrew..."
        brew install foundry-ai/foundry/foundry
    else
        echo "✅ Foundry Local already installed"
    fi
else
    echo "⚠️ Homebrew not found. Please install Foundry Local manually:"
    echo "   Visit: https://foundry.ai/docs/getting-started/installation"
fi

# Download SadTalker models
echo "🎬 Setting up SadTalker models..."
if [ -d "sadtalker_reference" ]; then
    cd sadtalker_reference
    if [ ! -d "checkpoints" ]; then
        echo "Downloading SadTalker models..."
        chmod +x scripts/download_models_macos.sh
        ./scripts/download_models_macos.sh
    else
        echo "✅ SadTalker models already downloaded"
    fi
    cd ..
else
    echo "⚠️ SadTalker reference directory not found. Please clone SadTalker first:"
    echo "   git clone https://github.com/OpenTalker/SadTalker.git sadtalker_reference"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backend/data/audio
mkdir -p backend/data/portraits
mkdir -p backend/artifacts/image
mkdir -p backend/artifacts/voice
mkdir -p backend/artifacts/text

# Create sample files if they don't exist
if [ ! -f "backend/data/portraits/sample_face.png" ]; then
    echo "Creating sample face image..."
    # Create a simple 256x256 PNG image
    python3 -c "
from PIL import Image
import numpy as np
img = Image.new('RGB', (256, 256), color='lightblue')
img.save('backend/data/portraits/sample_face.png')
print('Sample face image created')
"
fi

if [ ! -f "backend/data/audio/hello_2s.wav" ]; then
    echo "Creating sample audio file..."
    python3 -c "
import numpy as np
import soundfile as sf
import os
os.makedirs('backend/data/audio', exist_ok=True)
# Create a 2-second sine wave
sample_rate = 22050
duration = 2.0
t = np.linspace(0, duration, int(sample_rate * duration), False)
frequency = 440
audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
sf.write('backend/data/audio/hello_2s.wav', audio_data, sample_rate)
print('Sample audio file created')
"
fi

# Set up environment variables
echo "⚙️ Setting up environment..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Persona Wizard Configuration
DEBUG=True
LOG_LEVEL=INFO

# Foundry Local Configuration
FOUNDRY_LOCAL_ENABLED=True
FOUNDRY_LOCAL_MODEL_NAME=phi-3.5-mini

# TTS Configuration
TTS_MODEL=xtts-v2
TTS_DEVICE=cpu

# SadTalker Configuration
SADTALKER_PATH=./sadtalker_reference
SADTALKER_DEVICE=cpu

# File Paths
ARTIFACTS_DIR=./backend/artifacts
MODELS_DIR=./backend/models
DATA_DIR=./backend/data
EOF
    echo "✅ Environment file created"
else
    echo "✅ Environment file already exists"
fi

# Test the installation
echo "🧪 Testing installation..."
python3 -c "
import sys
sys.path.insert(0, 'backend')
try:
    from app.main import app
    from app.services.tts.xtts_real import RealXTTSService
    from app.services.lipsync.sadtalker_real import RealSadTalkerService
    from app.services.foundry.local_client import FoundryLocalClient
    print('✅ All services import successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the development servers:"
echo "  make dev"
echo ""
echo "Or start them individually:"
echo "  # Terminal 1: Start Foundry Local"
echo "  foundry service start"
echo ""
echo "  # Terminal 2: Start Backend"
echo "  source venv/bin/activate"
echo "  uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "  # Terminal 3: Start Frontend"
echo "  cd frontend && npm run dev"
echo ""
echo "The application will be available at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend: http://localhost:8000"
echo "  Foundry Local: http://127.0.0.1:53224"
