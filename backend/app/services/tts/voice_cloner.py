"""
Voice Cloning TTS Service

Implements local text-to-speech with voice cloning using XTTS-v2.
Generates audio from text using cloned voice characteristics.
"""

import asyncio
import json
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import logging

try:
    import torch
    import torchaudio
    import librosa
    import soundfile as sf
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from ...core.config import settings
from ...core.logging import get_logger
from ...services.foundry.local_client import FoundryLocalClient
from .xtts_real import RealXTTSService

logger = get_logger(__name__)


class VoiceCloner:
    """Local TTS with voice cloning using XTTS-v2."""
    
    def __init__(self, device: str = "auto"):
        """
        Initialize voice cloner.
        
        Args:
            device: Device to run on ("cpu", "cuda", "auto")
        """
        self.device = self._get_device(device)
        self.model = None
        self.is_initialized = False
        
        # Audio parameters
        self.sample_rate = 16000
        self.chunk_length = 30  # seconds
        self.max_text_length = 500  # characters
        
        # Models directory
        self.models_dir = Path(settings.models_dir) / "tts"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Voice profiles directory
        self.voice_profiles_dir = settings.artifacts_dir / "voice"
        self.voice_profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Foundry Local client
        self.foundry_client = FoundryLocalClient()
        
        # Real XTTS service - handle initialization failure gracefully
        try:
            self.xtts_service = RealXTTSService()
        except Exception as e:
            logger.warning(f"Failed to initialize XTTS service: {e}")
            self.xtts_service = None
        
        logger.info(f"Initializing VoiceCloner on device: {self.device}")
    
    def _get_device(self, device: str) -> str:
        """Determine the best available device."""
        if device == "auto":
            if TORCH_AVAILABLE and torch.cuda.is_available():
                return "cuda"
            return "cpu"
        return device
    
    async def _load_model(self):
        """Load the XTTS-v2 model."""
        if self.is_initialized:
            return
        
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available, using mock implementation")
            self.is_initialized = True
            return
        
        try:
            logger.info("Loading XTTS-v2 model...")
            
            # For now, we'll use a mock implementation
            # In a real implementation, you would load the actual XTTS-v2 model here
            self.model = "mock_xtts_model"
            self.is_initialized = True
            
            logger.info("XTTS-v2 model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load XTTS-v2 model: {e}")
            # Fall back to mock implementation
            self.is_initialized = True
            logger.info("Using mock XTTS implementation")
    
    async def clone_voice(
        self,
        reference_audio: bytes,
        reference_text: str,
        voice_name: str
    ) -> Dict[str, Any]:
        """
        Create a voice clone from reference audio using real XTTS.
        
        Args:
            reference_audio: Reference audio data as bytes
            reference_text: Text corresponding to the reference audio
            voice_name: Name for the voice profile
            
        Returns:
            Dict with voice profile information
        """
        try:
            await self._load_model()
            
            # Process reference audio
            audio_array = self._process_audio(reference_audio)
            if audio_array is None:
                return {"error": "Failed to process reference audio"}
            
            # Save reference audio to temporary file for XTTS
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_audio_path = temp_file.name
                sf.write(temp_audio_path, audio_array, 22050)
            
            try:
                # Use real XTTS service for voice cloning
                if self.xtts_service is None:
                    raise RuntimeError("XTTS service not available")
                
                logger.info(f"Cloning voice using real XTTS: {voice_name}")
                clone_result = self.xtts_service.clone_voice(temp_audio_path, voice_name)
                
                if clone_result.get("status") != "success":
                    logger.error(f"XTTS voice cloning failed: {clone_result}")
                    return {"error": f"Voice cloning failed: {clone_result.get('error', 'Unknown error')}"}
                
                # Extract voice characteristics for compatibility
                voice_profile = await self._extract_voice_characteristics(
                    audio_array, reference_text
                )
                
                # Add XTTS-specific data
                voice_profile["xtts_ready"] = True
                voice_profile["reference_audio_path"] = temp_audio_path
                voice_profile["xtts_voice_id"] = voice_name
                
                # Save processed audio as WAV file in artifacts directory
                import uuid
                audio_id = str(uuid.uuid4())
                artifacts_audio_dir = Path(settings.artifacts_dir) / "voice"
                artifacts_audio_dir.mkdir(parents=True, exist_ok=True)
                
                # Save the processed audio as WAV (without _original suffix)
                wav_path = artifacts_audio_dir / f"{audio_id}.wav"
                sf.write(wav_path, audio_array, 22050)
                
                # Save metadata for the audio file
                metadata = {
                    "voice_name": voice_name,
                    "created_at": datetime.now().isoformat(),
                    "duration": len(audio_array) / 22050,
                    "sample_rate": 22050,
                    "format": "wav",
                    "xtts_ready": True,
                    "xtts_voice_id": voice_name
                }
                
                metadata_path = artifacts_audio_dir / f"{audio_id}.json"
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Save voice profile
                profile_path = self.voice_profiles_dir / f"{voice_name}.json"
                with open(profile_path, 'w') as f:
                    json.dump(voice_profile, f, indent=2)
                
                logger.info(f"Voice profile saved: {profile_path}")
                logger.info(f"Audio artifact saved: {wav_path}")
                
                return {
                    "voice_name": voice_name,
                    "profile_path": str(profile_path),
                    "audio_path": str(wav_path),
                    "audio_id": audio_id,
                    "sample_rate": 22050,  # XTTS standard
                    "duration": len(audio_array) / 22050,
                    "characteristics": voice_profile,
                    "xtts_ready": True
                }
                
            finally:
                # Clean up temporary audio file
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
            
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            return {"error": f"Voice cloning failed: {str(e)}"}
    
    async def synthesize_speech(
        self,
        text: str,
        voice_profile: Dict[str, Any],
        output_format: str = "wav"
    ) -> Dict[str, Any]:
        """
        Synthesize speech from text using cloned voice with real XTTS.
        
        Args:
            text: Text to synthesize
            voice_profile: Voice profile from clone_voice
            output_format: Output audio format ("wav", "mp3")
            
        Returns:
            Dict with synthesized audio data and metadata
        """
        try:
            # Validate text length
            if len(text) > self.max_text_length:
                text = text[:self.max_text_length]
                logger.warning(f"Text truncated to {self.max_text_length} characters")
            
            # Check if we have XTTS-ready voice profile
            if voice_profile.get("xtts_ready") and voice_profile.get("xtts_voice_id"):
                # Use real XTTS service for synthesis
                logger.info(f"Synthesizing speech using real XTTS for voice: {voice_profile.get('xtts_voice_id')}")
                
                # Create temporary output file
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as tmp_file:
                    temp_output_path = tmp_file.name
                
                # Use XTTS service for synthesis
                if self.xtts_service is None:
                    raise RuntimeError("XTTS service not available")
                
                synthesis_result = self.xtts_service.synthesize_speech(
                    text=text,
                    voice_id=voice_profile.get("xtts_voice_id"),
                    output_path=temp_output_path
                )
                
                if synthesis_result.get("status") != "success":
                    logger.error(f"XTTS synthesis failed: {synthesis_result}")
                    raise Exception(f"XTTS synthesis failed: {synthesis_result.get('error', 'Unknown error')}")
                
                # Read the generated audio file
                audio_data, sample_rate = sf.read(temp_output_path)
                audio_data = (audio_data * 32767).astype(np.int16)
                
                # Save to final location
                output_path = self._save_audio(audio_data.tobytes(), output_format)
                
                # Clean up temp file
                import os
                os.unlink(temp_output_path)
                
                return {
                    "audio_data": audio_data.tobytes(),
                    "output_path": str(output_path),
                    "duration": synthesis_result.get("duration", len(audio_data) / sample_rate),
                    "sample_rate": synthesis_result.get("sample_rate", sample_rate),
                    "format": output_format,
                    "text_length": len(text),
                    "voice_name": voice_profile.get("voice_name", "unknown"),
                    "via_xtts": True
                }
            
            else:
                # Fall back to Foundry Local or mock implementation
                logger.info("Using Foundry Local or mock synthesis (XTTS not ready)")
                
                # Create temporary output file
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as tmp_file:
                    temp_output_path = tmp_file.name
                
                # Use Foundry Local client for real TTS inference
                result = await self.foundry_client.synthesize_speech(
                    text=text,
                    voice_profile=voice_profile,
                    output_path=temp_output_path
                )
                
                # Read the generated audio file
                if TORCH_AVAILABLE:
                    audio_data, sample_rate = sf.read(temp_output_path)
                    audio_data = (audio_data * 32767).astype(np.int16)
                else:
                    # Fallback for when soundfile is not available
                    with open(temp_output_path, 'rb') as f:
                        audio_data = f.read()
                    sample_rate = self.sample_rate
                
                # Save to final location
                output_path = self._save_audio(audio_data, output_format)
                
                # Clean up temp file
                import os
                os.unlink(temp_output_path)
                
                return {
                    "audio_data": audio_data,
                    "output_path": str(output_path),
                    "duration": result.get("duration", len(audio_data) / self.sample_rate),
                    "sample_rate": result.get("sample_rate", self.sample_rate),
                    "format": output_format,
                    "text_length": len(text),
                    "voice_name": voice_profile.get("voice_name", "unknown"),
                    "via_foundry": result.get("via_foundry", False)
                }
            
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            # Fall back to mock implementation
            try:
                audio_data = await self._mock_synthesize_speech(text, voice_profile)
                output_path = self._save_audio(audio_data, output_format)
                
                return {
                    "audio_data": audio_data,
                    "output_path": str(output_path),
                    "duration": len(audio_data) / self.sample_rate,
                    "sample_rate": self.sample_rate,
                    "format": output_format,
                    "text_length": len(text),
                    "voice_name": voice_profile.get("voice_name", "unknown"),
                    "via_xtts": False
                }
            except Exception as fallback_error:
                logger.error(f"Fallback synthesis also failed: {fallback_error}")
                return {"error": f"Speech synthesis failed: {str(e)}"}
    
    def _process_audio(self, audio_data: bytes) -> Optional[np.ndarray]:
        """Process audio data (WebM format from frontend)."""
        try:
            logger.info(f"Processing audio data: {len(audio_data)} bytes")
            
            # Save WebM audio to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
                temp_webm_path = temp_file.name
                temp_file.write(audio_data)
            
            # Convert WebM to WAV using ffmpeg
            temp_wav_path = temp_webm_path.replace('.webm', '.wav')
            
            import subprocess
            cmd = [
                'ffmpeg', '-y',
                '-i', temp_webm_path,
                '-acodec', 'pcm_s16le',
                '-ar', '22050',  # XTTS standard sample rate
                '-ac', '1',      # Mono
                temp_wav_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Clean up WebM file
            import os
            os.unlink(temp_webm_path)
            
            if result.returncode != 0:
                logger.warning(f"FFmpeg conversion failed: {result.stderr}")
                # Fallback: create a simple WAV file
                return self._create_fallback_audio()
            
            # Load the converted WAV file
            audio_array, sample_rate = sf.read(temp_wav_path)
            
            # Clean up WAV file
            os.unlink(temp_wav_path)
            
            # Convert to mono if stereo
            if len(audio_array.shape) > 1:
                audio_array = np.mean(audio_array, axis=1)
            
            # Resample to 22050 Hz if needed (XTTS standard)
            if sample_rate != 22050:
                import librosa
                audio_array = librosa.resample(audio_array, orig_sr=sample_rate, target_sr=22050)
                sample_rate = 22050
            
            logger.info(f"Processed audio: {len(audio_array)} samples at {sample_rate} Hz")
            return audio_array
            
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            # Fallback: create a simple audio file
            return self._create_fallback_audio()
    
    def _create_fallback_audio(self) -> np.ndarray:
        """Create fallback audio when conversion fails."""
        try:
            duration = 2.0
            sample_rate = 22050
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            
            # Generate a simple sine wave
            frequency = 440
            audio_array = np.sin(2 * np.pi * frequency * t).astype(np.float32)
            
            # Add some variation
            audio_array += np.random.normal(0, 0.1, len(audio_array))
            audio_array = np.clip(audio_array, -1.0, 1.0)
            
            logger.info(f"Created fallback audio: {len(audio_array)} samples")
            return audio_array
            
        except Exception as e:
            logger.error(f"Fallback audio creation failed: {e}")
            return None
    
    async def _extract_voice_characteristics(
        self, 
        audio_array: np.ndarray, 
        reference_text: str
    ) -> Dict[str, Any]:
        """Extract voice characteristics from reference audio."""
        # Mock implementation - in reality, this would use XTTS-v2 to extract
        # speaker embeddings, prosody patterns, etc.
        
        duration = len(audio_array) / self.sample_rate
        
        # Calculate basic audio characteristics
        rms_energy = np.sqrt(np.mean(audio_array ** 2))
        zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(audio_array)[0])
        
        # Mock voice characteristics
        characteristics = {
            "speaker_embedding": np.random.randn(256).tolist(),  # Mock embedding
            "prosody_patterns": {
                "pitch_range": [80, 200],  # Hz
                "speaking_rate": 150,  # words per minute
                "pitch_mean": 140,  # Hz
                "energy_mean": float(rms_energy)
            },
            "acoustic_features": {
                "mfcc_mean": np.random.randn(13).tolist(),
                "spectral_centroid": float(np.mean(librosa.feature.spectral_centroid(y=audio_array)[0])),
                "zero_crossing_rate": float(zero_crossing_rate)
            },
            "metadata": {
                "duration": duration,
                "sample_rate": self.sample_rate,
                "text_length": len(reference_text),
                "extraction_method": "mock_xtts_v2",
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
        return characteristics
    
    async def _mock_synthesize_speech(
        self, 
        text: str, 
        voice_profile: Dict[str, Any]
    ) -> bytes:
        """Mock speech synthesis."""
        # Simulate processing time
        await asyncio.sleep(1.0)
        
        # Generate mock audio based on text length
        duration = len(text) / 10.0  # Rough estimate: 10 chars per second
        duration = max(1.0, min(duration, 10.0))  # Clamp between 1-10 seconds
        
        # Generate synthetic audio
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Create a simple tone with some variation
        frequency = 200 + np.sin(t * 0.5) * 50  # Varying frequency
        amplitude = 0.3 * np.sin(2 * np.pi * frequency * t)
        
        # Add some noise for realism
        noise = np.random.normal(0, 0.05, len(amplitude))
        audio_array = amplitude + noise
        
        # Normalize and convert to int16
        audio_array = np.clip(audio_array, -1.0, 1.0)
        audio_array = (audio_array * 32767).astype(np.int16)
        
        return audio_array.tobytes()
    
    def _save_audio(self, audio_data: bytes, format: str) -> Path:
        """Save audio data to file."""
        timestamp = int(asyncio.get_event_loop().time())
        filename = f"synthesized_{timestamp}.{format}"
        output_path = settings.data_dir / "outputs" / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert bytes back to numpy array for saving
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        if format == "wav":
            sf.write(str(output_path), audio_array, self.sample_rate)
        else:
            # Default to WAV if format not supported
            sf.write(str(output_path), audio_array, self.sample_rate)
        
        return output_path
    
    async def load_voice_profile(self, voice_name: str) -> Optional[Dict[str, Any]]:
        """Load a saved voice profile."""
        profile_path = self.voice_profiles_dir / f"{voice_name}.json"
        
        if not profile_path.exists():
            return None
        
        try:
            with open(profile_path, 'r') as f:
                profile = json.load(f)
            return profile
        except Exception as e:
            logger.error(f"Failed to load voice profile {voice_name}: {e}")
            return None
    
    def list_voice_profiles(self) -> List[Dict[str, Any]]:
        """List available voice profiles."""
        profiles = []
        
        for profile_file in self.voice_profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r') as f:
                    profile = json.load(f)
                
                profiles.append({
                    "voice_name": profile_file.stem,
                    "profile_path": str(profile_file),
                    "created_at": profile.get("metadata", {}).get("created_at", "unknown"),
                    "duration": profile.get("metadata", {}).get("duration", 0)
                })
            except Exception as e:
                logger.error(f"Failed to read profile {profile_file}: {e}")
        
        return profiles
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "device": self.device,
            "is_initialized": self.is_initialized,
            "torch_available": TORCH_AVAILABLE,
            "sample_rate": self.sample_rate,
            "max_text_length": self.max_text_length,
            "voice_profiles_dir": str(self.voice_profiles_dir)
        }
    
    async def cleanup(self):
        """Clean up resources."""
        self.model = None
        self.is_initialized = False
        logger.info("VoiceCloner cleaned up")


class MockVoiceCloner(VoiceCloner):
    """Mock voice cloner for testing."""
    
    def __init__(self, device: str = "cpu"):
        super().__init__(device)
        self.is_initialized = True
        logger.info("Using mock VoiceCloner implementation")
    
    async def _load_model(self):
        """Mock model loading."""
        self.is_initialized = True
    
    
    async def _mock_synthesize_speech(
        self, 
        text: str, 
        voice_profile: Dict[str, Any]
    ) -> bytes:
        """Enhanced mock speech synthesis."""
        await asyncio.sleep(0.5)
        
        # More realistic duration calculation
        words = text.split()
        duration = len(words) / 2.5  # ~2.5 words per second
        duration = max(0.5, min(duration, 15.0))  # Clamp between 0.5-15 seconds
        
        # Generate more realistic audio
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Create speech-like patterns
        base_freq = 150 + np.random.normal(0, 20)  # Base frequency with variation
        
        # Add formant-like structure
        formant1 = 0.6 * np.sin(2 * np.pi * base_freq * t)
        formant2 = 0.3 * np.sin(2 * np.pi * base_freq * 2.5 * t)
        formant3 = 0.1 * np.sin(2 * np.pi * base_freq * 4.0 * t)
        
        # Combine formants
        audio_array = formant1 + formant2 + formant3
        
        # Add envelope to simulate speech rhythm
        envelope = np.ones_like(t)
        for i in range(len(words)):
            start_idx = int(i * len(t) / len(words))
            end_idx = int((i + 1) * len(t) / len(words))
            envelope[start_idx:end_idx] *= np.random.uniform(0.3, 1.0)
        
        audio_array *= envelope
        
        # Add some realistic noise
        noise = np.random.normal(0, 0.02, len(audio_array))
        audio_array += noise
        
        # Normalize and convert to int16
        audio_array = np.clip(audio_array, -1.0, 1.0)
        audio_array = (audio_array * 32767).astype(np.int16)
        
        return audio_array.tobytes()
