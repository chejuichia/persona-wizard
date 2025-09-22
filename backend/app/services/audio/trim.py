"""
Audio Trimming Utilities

Handles audio trimming and duration management for voice capture.
Implements short-first defaults with 5-20 second limits.
"""

import numpy as np
from typing import Tuple, Optional
from pathlib import Path
import wave
import io

from ...core.config import settings
from ...core.logging import get_logger

logger = get_logger(__name__)


class AudioTrimmer:
    """Audio trimming and duration management."""
    
    def __init__(
        self,
        min_duration: float = 5.0,
        max_duration: float = 20.0,
        target_duration: float = 10.0,
        sample_rate: int = 16000
    ):
        """
        Initialize audio trimmer.
        
        Args:
            min_duration: Minimum audio duration in seconds
            max_duration: Maximum audio duration in seconds
            target_duration: Target duration for optimal processing
            sample_rate: Audio sample rate
        """
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.target_duration = target_duration
        self.sample_rate = sample_rate
        
        logger.debug(f"AudioTrimmer initialized: min={min_duration}s, max={max_duration}s, target={target_duration}s")
    
    def trim_audio(
        self, 
        audio_data: bytes, 
        sample_rate: int = 16000,
        start_padding: float = 0.1,
        end_padding: float = 0.1
    ) -> Tuple[bytes, float]:
        """
        Trim audio to optimal duration for voice cloning.
        
        Args:
            audio_data: Raw audio data as bytes
            sample_rate: Sample rate of the audio
            start_padding: Padding to add at start in seconds
            end_padding: Padding to add at end in seconds
            
        Returns:
            Tuple of (trimmed_audio_bytes, duration_seconds)
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            duration = len(audio_array) / sample_rate
            
            logger.debug(f"Original audio duration: {duration:.2f}s")
            
            # Check if audio is too short
            if duration < self.min_duration:
                logger.warning(f"Audio too short: {duration:.2f}s < {self.min_duration}s")
                return audio_data, duration
            
            # Check if audio is too long
            if duration > self.max_duration:
                logger.info(f"Audio too long: {duration:.2f}s > {self.max_duration}s, trimming")
                audio_array = self._trim_to_duration(audio_array, sample_rate, self.max_duration)
                duration = len(audio_array) / sample_rate
            
            # Add padding
            if start_padding > 0 or end_padding > 0:
                audio_array = self._add_padding(audio_array, sample_rate, start_padding, end_padding)
                duration = len(audio_array) / sample_rate
            
            # Convert back to bytes
            trimmed_bytes = audio_array.astype(np.int16).tobytes()
            
            logger.debug(f"Trimmed audio duration: {duration:.2f}s")
            return trimmed_bytes, duration
            
        except Exception as e:
            logger.error(f"Audio trimming failed: {e}")
            return audio_data, len(audio_data) / sample_rate
    
    def _trim_to_duration(self, audio_array: np.ndarray, sample_rate: int, target_duration: float) -> np.ndarray:
        """Trim audio to target duration, keeping the middle portion."""
        target_samples = int(target_duration * sample_rate)
        
        if len(audio_array) <= target_samples:
            return audio_array
        
        # Keep the middle portion
        start_idx = (len(audio_array) - target_samples) // 2
        end_idx = start_idx + target_samples
        
        return audio_array[start_idx:end_idx]
    
    def _add_padding(self, audio_array: np.ndarray, sample_rate: int, start_padding: float, end_padding: float) -> np.ndarray:
        """Add silence padding to audio."""
        start_samples = int(start_padding * sample_rate)
        end_samples = int(end_padding * sample_rate)
        
        # Create silence arrays
        start_silence = np.zeros(start_samples, dtype=audio_array.dtype)
        end_silence = np.zeros(end_samples, dtype=audio_array.dtype)
        
        # Concatenate
        return np.concatenate([start_silence, audio_array, end_silence])
    
    def find_optimal_segment(
        self, 
        audio_data: bytes, 
        sample_rate: int = 16000,
        target_duration: Optional[float] = None
    ) -> Tuple[bytes, float, float, float]:
        """
        Find the optimal audio segment for voice cloning.
        
        Args:
            audio_data: Raw audio data as bytes
            sample_rate: Sample rate of the audio
            target_duration: Target duration (uses default if None)
            
        Returns:
            Tuple of (optimal_audio_bytes, start_time, end_time, duration)
        """
        try:
            if target_duration is None:
                target_duration = self.target_duration
            
            # Convert to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            total_duration = len(audio_array) / sample_rate
            
            if total_duration <= target_duration:
                # Audio is already optimal length
                return audio_data, 0.0, total_duration, total_duration
            
            # Find the best segment using energy analysis
            best_start, best_end = self._find_best_segment(
                audio_array, sample_rate, target_duration
            )
            
            # Extract optimal segment
            optimal_audio = audio_array[best_start:best_end]
            duration = len(optimal_audio) / sample_rate
            
            # Convert back to bytes
            optimal_bytes = optimal_audio.astype(np.int16).tobytes()
            
            start_time = best_start / sample_rate
            end_time = best_end / sample_rate
            
            logger.debug(f"Found optimal segment: {start_time:.2f}s - {end_time:.2f}s ({duration:.2f}s)")
            
            return optimal_bytes, start_time, end_time, duration
            
        except Exception as e:
            logger.error(f"Optimal segment finding failed: {e}")
            # Fallback to simple trimming
            trimmed_bytes, duration = self.trim_audio(audio_data, sample_rate)
            return trimmed_bytes, 0.0, duration, duration
    
    def _find_best_segment(
        self, 
        audio_array: np.ndarray, 
        sample_rate: int, 
        target_duration: float
    ) -> Tuple[int, int]:
        """Find the best audio segment using energy analysis."""
        target_samples = int(target_duration * sample_rate)
        frame_size = int(0.1 * sample_rate)  # 100ms frames
        
        # Calculate energy for each frame
        energies = []
        for i in range(0, len(audio_array) - frame_size, frame_size):
            frame = audio_array[i:i + frame_size]
            energy = np.sqrt(np.mean(frame.astype(np.float32) ** 2))
            energies.append(energy)
        
        if not energies:
            # Fallback to middle segment
            start_idx = (len(audio_array) - target_samples) // 2
            end_idx = start_idx + target_samples
            return start_idx, end_idx
        
        # Find the segment with highest average energy
        max_energy = 0
        best_start = 0
        best_end = target_samples
        
        for i in range(len(energies) - int(target_duration * 10) + 1):  # 10 frames per second
            segment_energy = np.mean(energies[i:i + int(target_duration * 10)])
            
            if segment_energy > max_energy:
                max_energy = segment_energy
                best_start = i * frame_size
                best_end = best_start + target_samples
        
        # Ensure we don't exceed audio bounds
        best_end = min(best_end, len(audio_array))
        best_start = max(0, best_end - target_samples)
        
        return best_start, best_end
    
    def validate_audio(self, audio_data: bytes, sample_rate: int = 16000) -> Tuple[bool, str]:
        """
        Validate audio data for voice cloning.
        
        Args:
            audio_data: Raw audio data as bytes
            sample_rate: Sample rate of the audio
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if audio data is empty
            if len(audio_data) == 0:
                return False, "Audio data is empty"
            
            # Convert to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            duration = len(audio_array) / sample_rate
            
            # Check duration
            if duration < self.min_duration:
                return False, f"Audio too short: {duration:.2f}s < {self.min_duration}s minimum"
            
            if duration > self.max_duration:
                return False, f"Audio too long: {duration:.2f}s > {self.max_duration}s maximum"
            
            # Check for silence
            audio_float = audio_array.astype(np.float32) / 32768.0
            rms_energy = np.sqrt(np.mean(audio_float ** 2))
            
            if rms_energy < 0.001:  # Very low energy threshold
                return False, "Audio appears to be silent or very quiet"
            
            # Check for clipping
            max_amplitude = np.max(np.abs(audio_array))
            if max_amplitude >= 32767:  # Near maximum 16-bit value
                return False, "Audio appears to be clipped (too loud)"
            
            return True, "Audio is valid"
            
        except Exception as e:
            return False, f"Audio validation failed: {str(e)}"
    
    def save_audio(self, audio_data: bytes, file_path: Path, sample_rate: int = 16000) -> bool:
        """
        Save audio data to WAV file.
        
        Args:
            audio_data: Raw audio data as bytes
            file_path: Path to save the file
            sample_rate: Sample rate of the audio
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save as WAV file
            with wave.open(str(file_path), 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data)
            
            logger.debug(f"Audio saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save audio to {file_path}: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get trimmer statistics."""
        return {
            "min_duration": self.min_duration,
            "max_duration": self.max_duration,
            "target_duration": self.target_duration,
            "sample_rate": self.sample_rate
        }