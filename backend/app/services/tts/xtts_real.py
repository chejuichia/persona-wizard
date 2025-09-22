"""
Real XTTS implementation for voice cloning and synthesis using Coqui TTS.
Based on official documentation: https://docs.coqui.ai/en/latest/
"""

import os
import torch
import torchaudio
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging
import tempfile
import subprocess

logger = logging.getLogger(__name__)

class RealXTTSService:
    """Real XTTS service for voice cloning and synthesis using Coqui TTS."""
    
    def __init__(self):
        self.device = self._get_device()
        self.model = None
        self.speaker_embeddings = {}
        self._load_model()
    
    def _get_device(self) -> str:
        """Get the appropriate device for inference."""
        # Force CPU usage due to MPS compatibility issues with XTTS
        # TODO: Re-enable MPS when PyTorch MPS supports all required operations
        return "cpu"
    
    def _load_model(self):
        """Load the XTTS model based on Coqui documentation."""
        try:
            # Try to load Coqui TTS library with XTTS-v2
            # According to docs: XTTS is the recommended model for voice cloning
            from TTS.api import TTS
            logger.info("Loading Coqui XTTS-v2 model for voice cloning...")
            
            # Fix PyTorch loading issue by setting weights_only=False
            import torch
            original_load = torch.load
            
            def safe_load(*args, **kwargs):
                kwargs.setdefault('weights_only', False)
                return original_load(*args, **kwargs)
            
            torch.load = safe_load
            
            try:
                # Initialize XTTS-v2 model as per Coqui documentation
                # Reference: https://docs.coqui.ai/en/latest/
                self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
                
                # Move to device if available
                if self.device != "cpu":
                    self.model = self.model.to(self.device)
                
                logger.info(f"Coqui XTTS-v2 model loaded successfully on {self.device}")
                
            finally:
                # Restore original torch.load
                torch.load = original_load
            
        except ImportError as e:
            logger.error(f"Coqui TTS library not available: {e}")
            raise RuntimeError("Coqui TTS library is required for voice cloning. Please install it with: pip install TTS")
        except Exception as e:
            logger.error(f"Failed to load Coqui XTTS-v2 model: {e}")
            raise RuntimeError(f"Failed to load XTTS model: {e}")
    
    def clone_voice(self, reference_audio_path: str, voice_id: str) -> Dict[str, Any]:
        """
        Clone voice from reference audio using Coqui XTTS-v2.
        
        Args:
            reference_audio_path: Path to reference audio file
            voice_id: Unique identifier for the voice
            
        Returns:
            Dictionary with cloning results
        """
        try:
            logger.info(f"Cloning voice from: {reference_audio_path}")
            
            # Convert WebM to WAV if needed (XTTS-v2 works best with WAV)
            if reference_audio_path.endswith('.webm'):
                wav_path = reference_audio_path.replace('.webm', '.wav')
                self._convert_webm_to_wav(reference_audio_path, wav_path)
                reference_audio_path = wav_path
            
            # Load reference audio to validate and get properties
            audio_data, sample_rate = torchaudio.load(reference_audio_path)
            if audio_data is None:
                raise ValueError(f"Could not load reference audio: {reference_audio_path}")
            
            # For Coqui XTTS-v2, we don't need to extract embeddings manually
            # The model handles voice cloning internally using the reference audio
            # We just need to store the reference audio path for synthesis
            
            # Store the reference audio path for XTTS synthesis
            self.speaker_embeddings[voice_id] = {
                "reference_audio_path": reference_audio_path,
                "sample_rate": sample_rate,
                "duration": audio_data.shape[1] / sample_rate
            }
            
            logger.info(f"Voice cloned successfully: {voice_id} (Coqui XTTS-v2 ready)")
            
            return {
                "status": "success",
                "voice_id": voice_id,
                "sample_rate": sample_rate,
                "duration": audio_data.shape[1] / sample_rate,
                "xtts_ready": True
            }
            
        except Exception as e:
            logger.error(f"Error cloning voice: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _convert_webm_to_wav(self, webm_path: str, wav_path: str):
        """Convert WebM audio to WAV format for XTTS compatibility."""
        try:
            # Use ffmpeg to convert WebM to WAV
            cmd = [
                'ffmpeg', '-y',
                '-i', webm_path,
                '-acodec', 'pcm_s16le',
                '-ar', '22050',  # XTTS standard sample rate
                '-ac', '1',      # Mono
                wav_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg conversion failed: {result.stderr}")
            
            logger.info(f"Converted {webm_path} to {wav_path}")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg conversion timed out after 30 seconds")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg for audio conversion")
        except Exception as e:
            raise RuntimeError(f"Error converting WebM to WAV: {e}")
    
    def synthesize_speech(
        self, 
        text: str, 
        voice_id: str, 
        output_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Synthesize speech using cloned voice with Coqui XTTS-v2.
        
        Args:
            text: Text to synthesize
            voice_id: ID of the cloned voice
            output_path: Path to save the audio
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with synthesis results
        """
        try:
            logger.info(f"Synthesizing speech: '{text[:50]}...' with voice {voice_id}")
            
            # Handle default voice case
            if voice_id == "default":
                logger.info("Using default voice synthesis without voice cloning")
                self.model.tts_to_file(
                    text=text,
                    language="en",
                    file_path=output_path
                )
            else:
                if voice_id not in self.speaker_embeddings:
                    raise ValueError(f"Voice {voice_id} not found. Please clone the voice first.")
                
                # Get speaker data
                speaker_data = self.speaker_embeddings[voice_id]
                reference_audio = speaker_data.get("reference_audio_path")
                
                if not reference_audio or not os.path.exists(reference_audio):
                    raise ValueError(f"Reference audio not found: {reference_audio}")
                
                # Use Coqui XTTS-v2 for real voice cloning as per their documentation
                # Reference: https://docs.coqui.ai/en/latest/
                logger.info("Using Coqui XTTS-v2 for real voice cloning synthesis")
                
                self.model.tts_to_file(
                    text=text,
                    speaker_wav=reference_audio,
                    language="en",
                    file_path=output_path
                )
            
            # Load the generated audio to get duration and verify
            audio_data, actual_sample_rate = torchaudio.load(output_path)
            duration = audio_data.shape[1] / actual_sample_rate
            
            logger.info(f"Coqui XTTS-v2 synthesis successful: {duration:.2f}s audio generated")
            
            return {
                "status": "success",
                "output_path": output_path,
                "duration": duration,
                "sample_rate": actual_sample_rate
            }
            
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return {
                "status": "error",
                "error": str(e)
            }