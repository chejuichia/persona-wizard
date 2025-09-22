#!/usr/bin/env python3
"""Pre-generate sample files for S0 demonstration."""

import logging
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_image():
    """Create a sample face image."""
    portraits_dir = settings.data_dir / "portraits"
    portraits_dir.mkdir(parents=True, exist_ok=True)
    
    sample_image = portraits_dir / "sample_face.png"
    
    # Create a simple face-like image
    img = Image.new('RGB', (512, 512), color='lightblue')
    
    # Draw a simple face
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Face outline
    draw.ellipse([100, 100, 412, 412], fill='peachpuff', outline='black', width=2)
    
    # Eyes
    draw.ellipse([150, 200, 180, 230], fill='white', outline='black', width=2)
    draw.ellipse([332, 200, 362, 230], fill='white', outline='black', width=2)
    draw.ellipse([160, 210, 170, 220], fill='black')
    draw.ellipse([342, 210, 352, 220], fill='black')
    
    # Nose
    draw.polygon([(256, 250), (246, 280), (266, 280)], fill='peachpuff', outline='black', width=1)
    
    # Mouth
    draw.arc([200, 300, 312, 350], 0, 180, fill='red', width=3)
    
    img.save(sample_image)
    logger.info(f"Created sample image: {sample_image}")
    return sample_image


def create_sample_audio():
    """Create a sample audio file."""
    audio_dir = settings.data_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    sample_audio = audio_dir / "hello_2s.wav"
    
    # Create a 2-second audio file with a simple tone
    sample_rate = settings.voice_sample_rate
    duration = 2.0
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Create a simple sine wave with some variation
    frequency = 440  # A4 note
    audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)
    
    # Add some envelope to make it more natural
    envelope = np.exp(-t * 2)  # Decay envelope
    audio_data *= envelope
    
    # Add some noise for realism
    noise = 0.01 * np.random.randn(len(audio_data))
    audio_data += noise
    
    # Normalize
    audio_data = audio_data / np.max(np.abs(audio_data)) * 0.8
    
    sf.write(str(sample_audio), audio_data, sample_rate)
    logger.info(f"Created sample audio: {sample_audio}")
    return sample_audio


def create_sample_video():
    """Create a sample video using the SadTalker adapter."""
    try:
        from app.services.lipsync.sadtalker_adapter import SadTalkerAdapter
        
        # Get sample files
        sample_image = settings.data_dir / "portraits" / "sample_face.png"
        sample_audio = settings.data_dir / "audio" / "hello_2s.wav"
        
        if not sample_image.exists() or not sample_audio.exists():
            logger.error("Sample files not found. Run create_sample_image and create_sample_audio first.")
            return None
        
        # Create output directory
        outputs_dir = settings.data_dir / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate sample video
        output_path = outputs_dir / "sample.mp4"
        adapter = SadTalkerAdapter(device="cpu")
        
        result = adapter.generate_video(
            image_path=sample_image,
            audio_path=sample_audio,
            output_path=output_path
        )
        
        if result.success:
            logger.info(f"Created sample video: {output_path}")
            logger.info(f"Duration: {result.duration_seconds:.2f}s, Size: {result.size_px}px, FPS: {result.fps}")
            return output_path
        else:
            logger.error(f"Failed to create sample video: {result.error}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to create sample video: {e}")
        return None


def main():
    """Main function."""
    logger.info("Creating sample files for S0...")
    
    # Create sample image
    sample_image = create_sample_image()
    
    # Create sample audio
    sample_audio = create_sample_audio()
    
    # Create sample video
    sample_video = create_sample_video()
    
    if sample_video:
        logger.info("✅ Sample files created successfully!")
        logger.info(f"Image: {sample_image}")
        logger.info(f"Audio: {sample_audio}")
        logger.info(f"Video: {sample_video}")
    else:
        logger.error("❌ Failed to create sample video")
        sys.exit(1)


if __name__ == "__main__":
    main()
