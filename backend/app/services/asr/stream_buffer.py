"""
Audio Stream Buffer

Manages audio data buffering for real-time ASR processing.
Implements circular buffering and audio accumulation for streaming transcription.
"""

import numpy as np
from typing import Optional, List
from collections import deque
import threading
import time

from ...core.logging import get_logger

logger = get_logger(__name__)


class AudioStreamBuffer:
    """Circular buffer for audio streaming with accumulation."""
    
    def __init__(self, max_duration: float = 30.0, sample_rate: int = 16000):
        """
        Initialize audio stream buffer.
        
        Args:
            max_duration: Maximum duration to buffer in seconds
            sample_rate: Audio sample rate in Hz
        """
        self.sample_rate = sample_rate
        self.max_samples = int(max_duration * sample_rate)
        self.buffer = deque(maxlen=self.max_samples)
        self.accumulated_audio = []
        self.lock = threading.Lock()
        self.last_activity = time.time()
        self.is_accumulating = False
        
        logger.debug(f"AudioStreamBuffer initialized: max_duration={max_duration}s, sample_rate={sample_rate}Hz")
    
    def add_audio(self, audio_data: bytes, sample_rate: int = 16000):
        """
        Add audio data to the buffer.
        
        Args:
            audio_data: Raw audio data as bytes
            sample_rate: Sample rate of the audio data
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Resample if necessary
            if sample_rate != self.sample_rate:
                audio_array = self._resample_audio(audio_array, sample_rate, self.sample_rate)
            
            with self.lock:
                # Add to circular buffer
                self.buffer.extend(audio_array)
                
                # Add to accumulated audio if we're in accumulation mode
                if self.is_accumulating:
                    self.accumulated_audio.extend(audio_array)
                
                self.last_activity = time.time()
                
        except Exception as e:
            logger.error(f"Failed to add audio to buffer: {e}")
    
    def start_accumulation(self):
        """Start accumulating audio for transcription."""
        with self.lock:
            self.is_accumulating = True
            self.accumulated_audio = []
            logger.debug("Started audio accumulation")
    
    def stop_accumulation(self):
        """Stop accumulating audio."""
        with self.lock:
            self.is_accumulating = False
            logger.debug("Stopped audio accumulation")
    
    def get_audio(self) -> Optional[np.ndarray]:
        """
        Get accumulated audio data.
        
        Returns:
            Numpy array of accumulated audio or None if no audio
        """
        with self.lock:
            if not self.accumulated_audio:
                return None
            
            # Convert to numpy array
            audio_array = np.array(self.accumulated_audio, dtype=np.float32)
            
            # Normalize to [-1, 1] range
            if audio_array.max() > 0:
                audio_array = audio_array / 32768.0
            
            return audio_array
    
    def get_recent_audio(self, duration: float = 5.0) -> Optional[np.ndarray]:
        """
        Get recent audio from the circular buffer.
        
        Args:
            duration: Duration of audio to retrieve in seconds
            
        Returns:
            Numpy array of recent audio or None if no audio
        """
        with self.lock:
            if not self.buffer:
                return None
            
            # Calculate number of samples to retrieve
            samples_to_get = min(int(duration * self.sample_rate), len(self.buffer))
            
            if samples_to_get == 0:
                return None
            
            # Get recent samples
            recent_audio = list(self.buffer)[-samples_to_get:]
            audio_array = np.array(recent_audio, dtype=np.float32)
            
            # Normalize to [-1, 1] range
            if audio_array.max() > 0:
                audio_array = audio_array / 32768.0
            
            return audio_array
    
    def clear(self):
        """Clear all buffered audio."""
        with self.lock:
            self.buffer.clear()
            self.accumulated_audio = []
            self.is_accumulating = False
            logger.debug("Audio buffer cleared")
    
    def get_duration(self) -> float:
        """Get the duration of accumulated audio in seconds."""
        with self.lock:
            if not self.accumulated_audio:
                return 0.0
            return len(self.accumulated_audio) / self.sample_rate
    
    def get_buffer_duration(self) -> float:
        """Get the duration of buffered audio in seconds."""
        with self.lock:
            return len(self.buffer) / self.sample_rate
    
    def is_silent(self, threshold: float = 0.01, duration: float = 1.0) -> bool:
        """
        Check if the recent audio is silent.
        
        Args:
            threshold: Silence threshold (RMS value)
            duration: Duration to check in seconds
            
        Returns:
            True if audio is silent, False otherwise
        """
        recent_audio = self.get_recent_audio(duration)
        if recent_audio is None:
            return True
        
        # Calculate RMS (Root Mean Square) energy
        rms = np.sqrt(np.mean(recent_audio ** 2))
        return rms < threshold
    
    def get_audio_level(self) -> float:
        """
        Get the current audio level (RMS).
        
        Returns:
            RMS audio level (0.0 to 1.0)
        """
        recent_audio = self.get_recent_audio(0.1)  # Last 100ms
        if recent_audio is None:
            return 0.0
        
        rms = np.sqrt(np.mean(recent_audio ** 2))
        return min(1.0, rms)
    
    def _resample_audio(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """
        Simple resampling implementation.
        
        Args:
            audio: Input audio array
            orig_sr: Original sample rate
            target_sr: Target sample rate
            
        Returns:
            Resampled audio array
        """
        if orig_sr == target_sr:
            return audio
        
        # Calculate resampling ratio
        ratio = target_sr / orig_sr
        new_length = int(len(audio) * ratio)
        
        # Simple linear interpolation
        old_indices = np.arange(len(audio))
        new_indices = np.linspace(0, len(audio) - 1, new_length)
        
        return np.interp(new_indices, old_indices, audio)
    
    def get_stats(self) -> dict:
        """Get buffer statistics."""
        with self.lock:
            return {
                "buffer_samples": len(self.buffer),
                "buffer_duration": self.get_buffer_duration(),
                "accumulated_samples": len(self.accumulated_audio),
                "accumulated_duration": self.get_duration(),
                "is_accumulating": self.is_accumulating,
                "last_activity": self.last_activity,
                "audio_level": self.get_audio_level()
            }
