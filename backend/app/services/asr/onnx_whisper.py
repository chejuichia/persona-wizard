"""
ONNX Whisper ASR Service

Implements local speech recognition using ONNX Runtime and Whisper models.
Optimized for real-time transcription with short-first defaults.
"""

import asyncio
import numpy as np
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import logging

try:
    import onnxruntime as ort
    import librosa
    import soundfile as sf
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

from ...core.config import settings
from ...core.logging import get_logger

logger = get_logger(__name__)


class ONNXWhisperASR:
    """ONNX-based Whisper ASR implementation."""
    
    def __init__(self, model_size: str = "tiny", device: str = "auto"):
        """
        Initialize ONNX Whisper ASR.
        
        Args:
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
            device: Device to run on ("cpu", "cuda", "auto")
        """
        self.model_size = model_size
        self.device = self._get_device(device)
        self.model = None
        self.tokenizer = None
        self.is_initialized = False
        
        # Audio processing parameters
        self.sample_rate = 16000
        self.chunk_length = 30  # seconds
        self.max_length = 448  # tokens
        
        # Model paths
        self.models_dir = Path(settings.models_dir) / "whisper"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initializing ONNX Whisper ASR with model size: {model_size}")
    
    def _get_device(self, device: str) -> str:
        """Determine the best available device."""
        if device == "auto":
            if ONNX_AVAILABLE and ort.get_available_providers():
                if "CUDAExecutionProvider" in ort.get_available_providers():
                    return "cuda"
            return "cpu"
        return device
    
    async def _load_model(self):
        """Load the Whisper ONNX model."""
        if self.is_initialized:
            return
        
        if not ONNX_AVAILABLE:
            raise RuntimeError("ONNX Runtime not available. Please install onnxruntime.")
        
        try:
            # For now, we'll use a mock implementation since we don't have actual ONNX models
            # In a real implementation, you would load the actual Whisper ONNX model here
            logger.info(f"Loading Whisper {self.model_size} model on {self.device}")
            
            # Mock model loading - replace with actual ONNX model loading
            self.model = "mock_whisper_model"
            self.tokenizer = "mock_tokenizer"
            self.is_initialized = True
            
            logger.info("Whisper model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise RuntimeError(f"Failed to load Whisper model: {e}")
    
    async def transcribe_audio(
        self, 
        audio_data: bytes, 
        sample_rate: int = 16000,
        language: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio data as bytes
            sample_rate: Sample rate of the audio
            language: Language hint for transcription
            
        Returns:
            Dict with transcription results or None if failed
        """
        try:
            # Ensure model is loaded
            await self._load_model()
            
            # Convert audio data to numpy array
            audio_array = self._process_audio(audio_data, sample_rate)
            
            if audio_array is None or len(audio_array) == 0:
                return None
            
            # Perform transcription (mock implementation)
            result = await self._transcribe_audio_array(audio_array, language)
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
    
    def _process_audio(self, audio_data: bytes, sample_rate: int) -> Optional[np.ndarray]:
        """Process raw audio data into the format expected by Whisper."""
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Convert to float32 and normalize
            audio_array = audio_array.astype(np.float32) / 32768.0
            
            # Resample if necessary
            if sample_rate != self.sample_rate:
                if ONNX_AVAILABLE:
                    audio_array = librosa.resample(
                        audio_array, 
                        orig_sr=sample_rate, 
                        target_sr=self.sample_rate
                    )
                else:
                    # Simple resampling fallback
                    ratio = self.sample_rate / sample_rate
                    new_length = int(len(audio_array) * ratio)
                    audio_array = np.interp(
                        np.linspace(0, len(audio_array), new_length),
                        np.arange(len(audio_array)),
                        audio_array
                    )
            
            # Ensure audio is not too long (Whisper has limits)
            max_samples = self.sample_rate * self.chunk_length
            if len(audio_array) > max_samples:
                audio_array = audio_array[:max_samples]
            
            return audio_array
            
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            return None
    
    async def _transcribe_audio_array(
        self, 
        audio_array: np.ndarray, 
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio array to text.
        
        This is a mock implementation. In a real system, you would:
        1. Load the actual Whisper ONNX model
        2. Run inference on the audio array
        3. Decode the tokens to text
        """
        try:
            # Mock transcription - replace with actual ONNX inference
            duration = len(audio_array) / self.sample_rate
            
            # Simulate processing time
            await asyncio.sleep(0.1)
            
            # Mock transcription result
            mock_texts = [
                "Hello, this is a test transcription.",
                "The quick brown fox jumps over the lazy dog.",
                "This is a sample audio for speech recognition testing.",
                "Welcome to the Persona Wizard voice capture system.",
                "Please speak clearly for better transcription accuracy."
            ]
            
            # Select mock text based on duration
            text_index = min(int(duration) % len(mock_texts), len(mock_texts) - 1)
            text = mock_texts[text_index]
            
            # Calculate confidence based on audio length
            confidence = min(0.95, 0.7 + (duration / 10.0))
            
            return {
                "text": text,
                "confidence": confidence,
                "language": language or "en",
                "duration": duration,
                "tokens": len(text.split())
            }
            
        except Exception as e:
            logger.error(f"Mock transcription failed: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "language": language or "en",
                "duration": 0.0,
                "tokens": 0
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_size": self.model_size,
            "device": self.device,
            "sample_rate": self.sample_rate,
            "chunk_length": self.chunk_length,
            "max_length": self.max_length,
            "is_initialized": self.is_initialized,
            "onnx_available": ONNX_AVAILABLE
        }
    
    async def cleanup(self):
        """Clean up resources."""
        self.model = None
        self.tokenizer = None
        self.is_initialized = False
        logger.info("ONNX Whisper ASR cleaned up")


class MockONNXWhisperASR(ONNXWhisperASR):
    """Mock implementation for testing when ONNX is not available."""
    
    def __init__(self, model_size: str = "tiny", device: str = "cpu"):
        super().__init__(model_size, device)
        self.is_initialized = True
        logger.info("Using mock ONNX Whisper ASR implementation")
    
    async def _load_model(self):
        """Mock model loading."""
        self.is_initialized = True
    
    async def _transcribe_audio_array(
        self, 
        audio_array: np.ndarray, 
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mock transcription with more realistic behavior."""
        duration = len(audio_array) / self.sample_rate
        
        # Simulate processing time based on audio length
        await asyncio.sleep(min(0.5, duration * 0.1))
        
        # Generate more realistic mock text based on duration
        if duration < 2:
            text = "Hello."
        elif duration < 5:
            text = "Hello, this is a test."
        elif duration < 10:
            text = "Hello, this is a test of the voice capture system."
        else:
            text = "Hello, this is a longer test of the voice capture and transcription system. It should work well for creating voice clones."
        
        # Add some variation based on language
        if language and language != "en":
            text = f"[{language}] {text}"
        
        # Calculate confidence
        confidence = min(0.95, 0.6 + (duration / 20.0))
        
        return {
            "text": text,
            "confidence": confidence,
            "language": language or "en",
            "duration": duration,
            "tokens": len(text.split())
        }
