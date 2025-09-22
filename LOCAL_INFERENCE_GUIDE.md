# Persona Bundle Local Inference Guide

## Overview

The Persona Wizard creates self-contained bundles that can be used for local inference without requiring the web interface. Each bundle contains all necessary artifacts, configurations, and a Python script for running the complete AI pipeline locally.

## Bundle Structure

A persona bundle contains:

```
persona_bundle/
├── persona.yaml              # Main persona configuration
├── run_local_inference.py    # Executable inference script
├── artifacts/                # All persona artifacts
│   ├── image/
│   │   └── face_ref.png      # Face reference for lip-sync
│   ├── voice/
│   │   ├── xtts_speaker.pth  # XTTS voice cloning model
│   │   ├── reference.wav     # Original voice sample
│   │   └── metadata.json     # Voice metadata
│   └── text/
│       └── style_profile.json # Text style profile
├── configs/                  # Service configurations
│   ├── llm.yaml             # LLM settings
│   ├── tts.yaml             # TTS settings
│   ├── sadtalker.yaml       # Lip-sync settings
│   ├── auido2exp.yaml       # SadTalker audio-to-expression config
│   ├── auido2pose.yaml      # SadTalker audio-to-pose config
│   ├── facerender.yaml      # SadTalker face renderer config
│   ├── facerender_still.yaml # SadTalker still face renderer config
│   └── similarity_Lm3D_all.mat # SadTalker 3DMM similarity matrix
├── models/                   # Symlinked model directories
│   ├── checkpoints/         # SadTalker model checkpoints (symlink)
│   ├── gfpgan/              # GFPGAN enhancement models (symlink)
│   └── config/              # SadTalker configuration files
└── app/                     # Self-contained application modules
    ├── services/            # AI service implementations
    ├── core/                # Core utilities and configuration
    └── utils/               # Utility functions
```

## Persona Configuration (persona.yaml)

The `persona.yaml` file contains the complete persona specification:

```yaml
id: unique-persona-id
name: "Persona Name"
created_utc: "2025-09-19T16:57:30.407198Z"

text:
  base_model: "phi-3.5-mini"
  style:
    mode: "profile"
    adapter_path: "artifacts/text/style_profile.json"
  generation:
    max_new_tokens: 256
    temperature: 0.7
    top_p: 0.9
  metadata:
    word_count: 150
    character_count: 750
    extraction_method: "uploaded"

voice:
  tts_engine: "xtts-v2"
  speaker_profile: "artifacts/voice/xtts_speaker.pth"
  sample_rate_hz: 16000
  metadata:
    language: "en"
    duration: 5.2
    reference_text: "Hello, this is my voice sample"
    speaking_rate: "medium"
    pitch: "neutral"
    energy: "calm"
    extraction_method: "uploaded"

image:
  face_ref: "artifacts/image/face_ref.png"
  metadata:
    extraction_method: "uploaded"

video:
  lipsync_engine: "sadtalker"
  mode: "short"
  size_px: 256
  fps: 12
  enhancer: "off"

guardrails:
  enabled: true
  blocked_categories:
    - "sexual-minors"
    - "graphic-violence"
    - "self-harm"
    - "illegal-instructions"
  max_output_chars: 1200
  regex_blocklist:
    - "(?i)credit card number\\b"
    - "(?i)social security number\\b"
```

## Usage Methods

### Method 1: Direct Script Execution

1. **Extract the bundle:**
   ```bash
   unzip persona_*.zip
   cd persona_*/
   ```

2. **Run inference:**
   ```bash
   # Generate full video (text + voice + lip-sync)
   python run_local_inference.py "Hello, tell me about yourself"
   
   # Generate with custom output directory
   python run_local_inference.py "Hello, tell me about yourself" --output-dir my_outputs
   
   # Generate with specific prompt
   python run_local_inference.py "a 20-second elevator pitch for the multi-modal AI persona wizard"
   ```

### Method 2: Programmatic Usage

```python
import zipfile
import tempfile
import subprocess
from pathlib import Path

# Extract bundle
with zipfile.ZipFile("persona_*.zip", 'r') as zip_ref:
    zip_ref.extractall("extracted_persona")

# Run inference
result = subprocess.run([
    "python", "run_local_inference.py", 
    "Your prompt here",
    "--output-dir", "outputs"
], cwd="extracted_persona")

print(f"Return code: {result.returncode}")
```

### Method 3: Using the Bundle Builder API

```python
from backend.app.services.bundle.builder import BundleBuilder

# Create a new bundle
builder = BundleBuilder()
bundle_path = builder.build_persona_bundle(
    persona_id="test-persona",
    persona_config=persona_config,
    artifacts_dir="artifacts"
)

# Extract and run
import zipfile
with zipfile.ZipFile(bundle_path, 'r') as zip_ref:
    zip_ref.extractall("extracted_persona")

# Run inference
subprocess.run(["python", "run_local_inference.py", "Your prompt"], 
               cwd="extracted_persona")
```

## Complete AI Pipeline

The `run_local_inference.py` script implements a complete AI pipeline:

### 1. Text Generation
- Uses Foundry Local with Phi-3.5-mini model
- Applies persona-specific style profiles
- Generates natural language responses

### 2. Voice Synthesis
- Loads XTTS-v2 voice cloning model
- Clones voice from reference audio sample
- Synthesizes speech with cloned voice characteristics

### 3. Video Generation
- Uses SadTalker for lip-sync video generation
- Implements the complete SadTalker pipeline:
  - **Preprocessing**: 3DMM extraction from face image
  - **Audio Processing**: Audio-to-facial-coefficient mapping
  - **Video Generation**: Face animation with lip-sync
- Applies GFPGAN enhancement for better face quality

## Output Files

The inference script generates:

- **Text Output**: Generated text response (logged to console)
- **Audio Output**: `voice_output.wav` (synthesized speech)
- **Video Output**: `output_video.mp4` (talking avatar video)

All outputs are saved to the specified output directory (`outputs/` by default).

## Performance Characteristics

### Processing Times (CPU-based)
- **Text Generation**: 2-3 seconds
- **Voice Synthesis**: 15-30 seconds (depending on length)
- **Video Generation**: 15-30 minutes (depending on number of frames)
- **Total Pipeline**: 30 minutes for typical use case

### Resource Requirements
- **RAM**: 8GB+ recommended (models load ~4GB)
- **Storage**: 10GB+ for models and dependencies
- **CPU**: Multi-core recommended for video processing
- **GPU**: Optional (CPU processing is stable and reliable)

## Configuration Customization

You can modify the configuration files before running inference:

### LLM Configuration (`configs/llm.yaml`)
```yaml
provider: "foundry-local"
model: "phi-3.5-mini"
max_tokens: 256
temperature: 0.7
```

### TTS Configuration (`configs/tts.yaml`)
```yaml
engine: "xtts-v2"
model_path: "artifacts/voice/xtts_speaker.pth"
sample_rate: 16000
device: "auto"
```

### SadTalker Configuration (`configs/sadtalker.yaml`)
```yaml
device: "cpu"
size: 256
old_version: false
preprocess: "crop"
```

## Dependencies

The local inference script requires:

- **Python 3.11+**
- **PyTorch** (for AI models)
- **Transformers** (for XTTS-v2)
- **SadTalker** (for lip-sync)
- **Foundry Local** (for text generation)
- **PyYAML** (for configuration)
- **NumPy, OpenCV, PIL** (for image processing)
- **Librosa, SoundFile** (for audio processing)

## Current Implementation Status

✅ **Fully Implemented**:
- Complete text generation pipeline
- XTTS-v2 voice cloning and synthesis
- SadTalker lip-sync video generation
- Self-contained bundle creation
- Error handling and logging

✅ **Working Features**:
- Multi-modal AI pipeline (text → voice → video)
- Persona-specific voice cloning
- Realistic lip-sync video generation
- Local inference without cloud dependencies

## Example Workflow

1. **Create Persona**: Use the web interface to upload text, image, and voice
2. **Build Bundle**: Click "Build Persona Bundle" to create the zip file
3. **Download Bundle**: Download the `persona_*.zip` file
4. **Extract & Run**: Extract and run local inference as shown above
5. **View Results**: Check the `outputs/` directory for generated video

## Advanced Usage

### Custom Inference Pipeline

You can create custom inference scripts that use the persona artifacts directly:

```python
import yaml
import json
from pathlib import Path

# Load persona configuration
with open("persona.yaml", 'r') as f:
    persona_config = yaml.safe_load(f)

# Load voice profile
voice_profile_path = "artifacts/voice/xtts_speaker.pth"

# Load text style profile
with open("artifacts/text/style_profile.json", 'r') as f:
    style_profile = json.load(f)

# Use these artifacts for custom inference...
```

### Batch Processing

```python
import subprocess
from pathlib import Path

# Process multiple prompts
prompts = [
    "Hello, how are you?",
    "Tell me about artificial intelligence",
    "What's your favorite hobby?"
]

for i, prompt in enumerate(prompts):
    result = subprocess.run([
        "python", "run_local_inference.py", 
        prompt,
        "--output-dir", f"outputs/batch_{i}"
    ])
    print(f"Processed prompt {i+1}: {result.returncode}")
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Model Loading**: Check that model files are present and accessible
3. **Memory Issues**: Ensure sufficient RAM (8GB+ recommended)
4. **Processing Time**: Video generation takes 15-30 minutes on CPU

### Debug Mode

Enable debug logging by setting environment variable:
```bash
export DEBUG=True
python run_local_inference.py "Your prompt"
```

### Performance Optimization

- Use GPU if available (modify device settings in configs)
- Reduce video resolution for faster processing
- Use shorter audio samples for voice cloning
- Process multiple prompts in parallel (if sufficient resources)

This approach gives you full control over the inference pipeline while leveraging the pre-processed persona artifacts and complete AI model integration.