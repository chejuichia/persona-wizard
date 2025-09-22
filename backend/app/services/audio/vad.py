"""
Voice Activity Detection

Implements voice activity detection for audio streams.
Uses energy-based detection with configurable thresholds.
"""

import numpy as np
from typing import List, Tuple
from collections import deque
import time

from ...core.logging import get_logger

logger = get_logger(__name__)


class VoiceActivityDetector:
    """Voice Activity Detection using energy-based analysis."""
    
    def __init__(
        self,
        energy_threshold: float = 0.01,
        silence_duration: float = 0.5,
        min_speech_duration: float = 0.1,
        frame_size: int = 1024,
        sample_rate: int = 16000
    ):
        """
        Initialize Voice Activity Detector.
        
        Args:
            energy_threshold: Energy threshold for speech detection
            silence_duration: Duration of silence to consider speech ended
            min_speech_duration: Minimum duration for valid speech
            frame_size: Frame size for analysis
            sample_rate: Audio sample rate
        """
        self.energy_threshold = energy_threshold
        self.silence_duration = silence_duration
        self.min_speech_duration = min_speech_duration
        self.frame_size = frame_size
        self.sample_rate = sample_rate
        
        # State tracking
        self.is_speaking = False
        self.speech_start_time = None
        self.silence_start_time = None
        self.energy_history = deque(maxlen=10)  # Keep last 10 energy values
        
        # Adaptive threshold
        self.adaptive_threshold = energy_threshold
        self.noise_floor = energy_threshold * 0.5
        
        logger.debug(f"VAD initialized: threshold={energy_threshold}, silence_duration={silence_duration}s")
    
    def detect_voice_activity(self, audio_data: bytes) -> bool:
        """
        Detect voice activity in audio data.
        
        Args:
            audio_data: Raw audio data as bytes
            
        Returns:
            True if voice activity detected, False otherwise
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Convert to float and normalize
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # Calculate energy for this frame
            energy = self._calculate_energy(audio_float)
            
            # Update energy history
            self.energy_history.append(energy)
            
            # Update adaptive threshold
            self._update_adaptive_threshold()
            
            # Detect voice activity
            is_voice = self._analyze_voice_activity(energy)
            
            # Update state
            self._update_state(is_voice)
            
            return self.is_speaking
            
        except Exception as e:
            logger.error(f"VAD error: {e}")
            return False
    
    def _calculate_energy(self, audio: np.ndarray) -> float:
        """Calculate RMS energy of audio frame."""
        if len(audio) == 0:
            return 0.0
        
        # Calculate RMS (Root Mean Square) energy
        rms = np.sqrt(np.mean(audio ** 2))
        return rms
    
    def _update_adaptive_threshold(self):
        """Update adaptive threshold based on recent energy history."""
        if len(self.energy_history) < 5:
            return
        
        # Calculate noise floor from recent history
        recent_energies = list(self.energy_history)[-5:]
        noise_floor = np.percentile(recent_energies, 20)  # 20th percentile
        
        # Update adaptive threshold
        self.adaptive_threshold = max(
            self.energy_threshold,
            noise_floor * 3.0  # 3x noise floor
        )
        
        # Update noise floor
        self.noise_floor = noise_floor
    
    def _analyze_voice_activity(self, energy: float) -> bool:
        """Analyze if current frame contains voice activity."""
        # Use adaptive threshold
        threshold = self.adaptive_threshold
        
        # Additional checks
        if energy < threshold:
            return False
        
        # Check for sudden energy increase (voice onset)
        if len(self.energy_history) >= 2:
            energy_increase = energy - self.energy_history[-2]
            if energy_increase > threshold * 0.5:
                return True
        
        # Check if energy is consistently above threshold
        if len(self.energy_history) >= 3:
            recent_energies = list(self.energy_history)[-3:]
            if all(e > threshold * 0.8 for e in recent_energies):
                return True
        
        return energy > threshold
    
    def _update_state(self, is_voice: bool):
        """Update VAD state based on voice activity."""
        current_time = time.time()
        
        if is_voice:
            if not self.is_speaking:
                # Speech started
                self.is_speaking = True
                self.speech_start_time = current_time
                self.silence_start_time = None
                logger.debug("Speech started")
            else:
                # Continue speaking
                pass
        else:
            if self.is_speaking:
                if self.silence_start_time is None:
                    # Start silence timer
                    self.silence_start_time = current_time
                else:
                    # Check if silence duration exceeded
                    silence_duration = current_time - self.silence_start_time
                    if silence_duration >= self.silence_duration:
                        # Check if we had enough speech
                        if self.speech_start_time:
                            speech_duration = self.silence_start_time - self.speech_start_time
                            if speech_duration >= self.min_speech_duration:
                                logger.debug(f"Speech ended after {speech_duration:.2f}s")
                            else:
                                logger.debug(f"Speech too short ({speech_duration:.2f}s), ignoring")
                        
                        # Reset state
                        self.is_speaking = False
                        self.speech_start_time = None
                        self.silence_start_time = None
            else:
                # Continue silence
                pass
    
    def reset(self):
        """Reset VAD state."""
        self.is_speaking = False
        self.speech_start_time = None
        self.silence_start_time = None
        self.energy_history.clear()
        self.adaptive_threshold = self.energy_threshold
        self.noise_floor = self.energy_threshold * 0.5
        logger.debug("VAD state reset")
    
    def get_speech_segments(self, audio_data: bytes, sample_rate: int = 16000) -> List[Tuple[float, float]]:
        """
        Get speech segments from audio data.
        
        Args:
            audio_data: Raw audio data as bytes
            sample_rate: Audio sample rate
            
        Returns:
            List of (start_time, end_time) tuples for speech segments
        """
        # Convert to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        audio_float = audio_array.astype(np.float32) / 32768.0
        
        # Process in frames
        frame_samples = int(self.sample_rate * 0.1)  # 100ms frames
        segments = []
        current_segment = None
        
        for i in range(0, len(audio_float), frame_samples):
            frame = audio_float[i:i + frame_samples]
            if len(frame) == 0:
                break
            
            # Calculate energy
            energy = self._calculate_energy(frame)
            
            # Check for voice activity
            is_voice = energy > self.adaptive_threshold
            
            frame_time = i / sample_rate
            
            if is_voice:
                if current_segment is None:
                    current_segment = [frame_time, frame_time]
                else:
                    current_segment[1] = frame_time
            else:
                if current_segment is not None:
                    # End current segment
                    duration = current_segment[1] - current_segment[0]
                    if duration >= self.min_speech_duration:
                        segments.append(tuple(current_segment))
                    current_segment = None
        
        # Add final segment if it exists
        if current_segment is not None:
            duration = current_segment[1] - current_segment[0]
            if duration >= self.min_speech_duration:
                segments.append(tuple(current_segment))
        
        return segments
    
    def get_stats(self) -> dict:
        """Get VAD statistics."""
        return {
            "is_speaking": self.is_speaking,
            "energy_threshold": self.energy_threshold,
            "adaptive_threshold": self.adaptive_threshold,
            "noise_floor": self.noise_floor,
            "energy_history_length": len(self.energy_history),
            "speech_start_time": self.speech_start_time,
            "silence_start_time": self.silence_start_time
        }
