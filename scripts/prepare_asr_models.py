#!/usr/bin/env python3
"""Prepare ASR models for local processing."""

import argparse
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_whisper_onnx(model_size: str = "tiny"):
    """Download Whisper ONNX model."""
    try:
        import onnxruntime as ort
        
        # For S0, we'll just create a placeholder
        # In later phases, this will download actual ONNX models
        models_dir = settings.models_dir / "whisper"
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a placeholder file
        placeholder = models_dir / f"whisper_{model_size}.onnx"
        placeholder.touch()
        
        logger.info(f"Created placeholder for Whisper {model_size} ONNX model: {placeholder}")
        return True
        
    except ImportError:
        logger.warning("ONNX Runtime not available. Install with: pip install onnxruntime")
        return False
    except Exception as e:
        logger.error(f"Failed to prepare Whisper ONNX model: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Prepare ASR models")
    parser.add_argument("--model", choices=["tiny", "base", "small"], default="tiny",
                       help="Whisper model size")
    parser.add_argument("--onnx", action="store_true", help="Download ONNX version")
    
    args = parser.parse_args()
    
    logger.info(f"Preparing ASR models (size: {args.model})...")
    
    success = True
    
    if args.onnx:
        success &= download_whisper_onnx(args.model)
    
    if success:
        logger.info("✅ ASR models prepared successfully!")
    else:
        logger.error("❌ Failed to prepare some ASR models")
        sys.exit(1)


if __name__ == "__main__":
    main()
