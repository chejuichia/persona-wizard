![future](thefuture.png)

# Persona Wizard

## TL;DR

*Everyone should own their digital identity and persona, and they can do that through the Multi-Modal Persona Wizard.*

**Persona Wizard** is an AI prototype that creates talking avatars from a voice, text, and photo sample. Give it a text prompt, and it generates a realistic video of a person responding with cloned voice and lip-synced movements. Think of it as "deepfake for good" - creating personalized AI assistants, virtual presenters, or educational content with just a few clicks.

![demogif](https://github.com/user-attachments/assets/4100c792-6052-4f9a-a9ba-b78203f43bba)

**What it does:**
- Users  are guided through voice recording, text and image upload
- Analyze text, voice, and image and prepare them for cloning
- Creates a video animating the portrait speaking the response
- All processing happens locally on your computer

https://github.com/user-attachments/assets/169106e3-6b6b-4c51-aee5-0dd1fb56ceba

**Perfect for:** Content creators, educators, developers,robotics teams, or anyone wanting to create and own their personalized AI avatars without complex setup.

<img width="1014" height="660" alt="Screenshot 2025-09-21 at 6 38 05 PM" src="https://github.com/user-attachments/assets/67d3fee6-0038-46b2-9183-7603d02efa0d" />

---

## Technical Architecture

<img width="3840" height="1337" alt="persona wizard | Mermaid Chart-2025-09-21-143209" src="https://github.com/user-attachments/assets/92e5ce6b-688e-42d1-95ae-f8c9fc56aaaa" />

### Core Stack
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python 3.11+ + Pydantic
- **AI Pipeline**: Multi-modal processing with voice cloning, text generation, and video synthesis
- **Deployment**: Docker-ready with comprehensive automation

### AI Models & Services

#### 1. Text Generation Pipeline
- **Model**: Microsoft Phi-3.5-mini (via Foundry Local)
- **Purpose**: Answers user prompts in natural language responses
- **Integration**: RESTful API with automatic model management
- **Performance**: ~2-3 seconds for typical responses

#### 2. Voice Synthesis Pipeline
- **Model**: Coqui XTTS-v2 (Text-to-Speech)
- **Capabilities**: Voice cloning from 3-second reference audio
- **Output**: High-quality WAV audio (16kHz, mono)
- **Processing**: CPU-optimized with MPS fallback for Apple Silicon

#### 3. Lip-Sync Video Generation Pipeline
- **Model**: SadTalker (Official `sadtalker-z` package)
- **Components**:
  - `CropAndExtract`: 3DMM extraction from face images
  - `Audio2Coeff`: Audio-to-facial-coefficient mapping
  - `AnimateFromCoeff`: Video generation from coefficients
- **Enhancement**: GFPGAN for face quality improvement
- **Output**: MP4 video with synchronized lip movements

### Inference Pipeline

```
User Input → Text Generation → Voice Synthesis → Video Generation → Output
     ↓              ↓              ↓              ↓
  [Prompt]    [LLM Response]   [Cloned Voice]  [Lip-Sync Video]
```

### Service Integration

#### Foundry Local Integration
- **Purpose**: Local LLM inference without cloud dependencies
- **Model Management**: Automatic model downloading and caching
- **API**: HTTP-based with automatic retry logic
- **Configuration**: YAML-based model and service configuration

#### Bundle System
- **Purpose**: Self-contained persona packages for deployment
- **Components**: 
  - `run_local_inference.py`: Standalone inference script
  - Model artifacts (voice, face, configs)
  - Symlinked SadTalker models for prototype but can be configured to be copied into bundle
- **Deployment**: ZIP-based distribution with dependency resolution

### Performance Characteristics

#### Inference Processing Times (CPU-based)
**GPUs can enable streaming and optimized times
- **Text Generation**: 2-3 seconds
- **Voice Synthesis**: 15-30 seconds (depending on length)
- **Video Generation**: 15-30 minutes (depending on number of frames)
- **Total Pipeline**: 30 minutes for typical use case

#### Resource Requirements
- **RAM**: 8GB+ recommended (models load ~4GB)
- **Storage**: 10GB+ for models and dependencies
- **CPU**: Multi-core recommended for video processing
- **GPU**: Optional

#### Configuration Management
- **Environment Variables**: `.env` file with sensible defaults
- **Service Discovery**: Automatic service detection and configuration
- **Model Paths**: Dynamic path resolution for different environments
- **Device Detection**: Automatic CPU/GPU detection and configuration

### API Design

#### RESTful Endpoints
- **Health Check**: `/healthz` - Service status and diagnostics
- **Device Info**: `/device` - Hardware capabilities and configuration
- **Persona Management**: CRUD operations for persona entities
- **Preview Generation**: Real-time content generation with progress tracking

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- FFmpeg
- Foundry Local
- 8GB+ RAM

### Step-by-Step Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/chejuichia/persona-wizard.git
cd persona-wizard
```

#### 2. Install System Dependencies

**macOS:**
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install python@3.11 node@18 ffmpeg

# Install Foundry Local
brew install foundry-ai/foundry/foundry
```

**Ubuntu/Debian:**
```bash
# Update package list
sudo apt update

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# Install FFmpeg
sudo apt install ffmpeg

# Install Foundry Local
# Download from: https://foundry.ai/docs/installation
```

**Windows:**
```bash
# Install Python 3.11 from python.org
# Install Node.js 18 from nodejs.org
# Install FFmpeg from ffmpeg.org
# Install Foundry Local from foundry.ai
```

#### 3. Verify Prerequisites
```bash
# Check Python version
python3 --version  # Should be 3.11+

# Check Node.js version
node --version     # Should be 18+

# Check FFmpeg
ffmpeg -version

# Check Foundry Local
foundry --version
```

#### 4. Run the Setup Script
```bash
# Make setup script executable
chmod +x setup.sh

# Run the automated setup
./setup.sh
```

This automated script will:
- Create Python virtual environment (`venv/`)
- Install all Python dependencies from `requirements.txt`
- Download SadTalker AI models (~10GB) to `backend/models/sadtalker/`
- Set up Foundry Local service
- Create necessary directories (`backend/data/`, `frontend/`)
- Install Node.js dependencies (`frontend/node_modules/`)

#### 5. Start All Services

**Option A: Start all services at once (recommended)**
```bash
make dev
```

**Option B: Start services individually**
```bash
# Terminal 1: Start Foundry Local
foundry local

# Terminal 2: Start Backend API
cd ../persona-wizard
source venv/bin/activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Start Frontend
cd ../persona-wizard/frontend
npm run dev
```

#### 6. Verify Services Are Running
```bash
# Check if services are responding
curl http://localhost:8000/healthz  # Backend health check
curl http://localhost:3000          # Frontend (should return HTML)
curl http://localhost:53224         # Foundry Local (if running on default port)

# Check running processes
ps aux | grep -E "(uvicorn|next|foundry)"
```

#### 7. Access the Application
- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz
- **Device Info**: http://localhost:8000/device

#### 8. Test the Complete Pipeline

**Step 8a: Create a Persona**
1. Open http://localhost:3000 in your browser
2. Click "Start Creating Your Persona"
3. Record your voice
4. Enter a sample of your writing
5. Upload a clear face image (PNG/JPG, front-facing)
6. Click "Generate Persona"

**Step 8b: Build Persona Bundle**
1. In the persona list, click "Build Bundle"
2. Wait for bundle creation (may take 1-2 minutes)
3. Download the `persona_*.zip` file

**Step 8c: Test Local Inference**
```bash
# Extract the bundle
unzip persona_*.zip
cd persona_*/

# Run local inference
python run_local_inference.py "Hello, tell me about artificial intelligence"

# Check outputs
ls -la outputs/
# Should see: voice_output.wav and output_video.mp4
```

**Step 8d: Test Web Interface**
1. Go back to http://localhost:3000
2. Select your persona
3. Enter a prompt: e.g. "a 20-second elevator pitch for the multi-modal AI persona wizard"
4. Click "Generate Video"
5. Wait for processing (15-30 minutes)
6. View the video

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with proper error handling
4. Add comprehensive tests
5. Submit a pull request with detailed description

