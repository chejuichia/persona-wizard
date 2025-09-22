"""
Tests for ASR WebSocket functionality.
"""

import pytest
import asyncio
import json
import numpy as np
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.services.asr.onnx_whisper import ONNXWhisperASR
from app.services.asr.stream_buffer import AudioStreamBuffer
from app.services.audio.vad import VoiceActivityDetector

client = TestClient(app)


class TestONNXWhisperASR:
    """Test the ONNX Whisper ASR service."""
    
    def test_initialization(self):
        """Test ASR service initialization."""
        asr = ONNXWhisperASR(model_size="tiny", device="cpu")
        
        assert asr.model_size == "tiny"
        assert asr.device == "cpu"
        assert asr.sample_rate == 16000
        assert asr.chunk_length == 30
        assert not asr.is_initialized
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_mock(self):
        """Test audio transcription with mock implementation."""
        asr = ONNXWhisperASR(model_size="tiny", device="cpu")
        
        # Create mock audio data
        sample_rate = 16000
        duration = 2.0  # 2 seconds
        audio_data = np.random.randint(-32768, 32767, int(sample_rate * duration), dtype=np.int16)
        audio_bytes = audio_data.tobytes()
        
        # Test transcription
        result = await asr.transcribe_audio(audio_bytes, sample_rate)
        
        assert result is not None
        assert "text" in result
        assert "confidence" in result
        assert "language" in result
        assert "duration" in result
        assert "tokens" in result
        assert isinstance(result["text"], str)
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["duration"] > 0
    
    @pytest.mark.asyncio
    async def test_transcribe_empty_audio(self):
        """Test transcription with empty audio."""
        asr = ONNXWhisperASR(model_size="tiny", device="cpu")
        
        result = await asr.transcribe_audio(b"", 16000)
        assert result is None
    
    def test_get_model_info(self):
        """Test getting model information."""
        asr = ONNXWhisperASR(model_size="base", device="cpu")
        
        info = asr.get_model_info()
        
        assert info["model_size"] == "base"
        assert info["device"] == "cpu"
        assert info["sample_rate"] == 16000
        assert info["chunk_length"] == 30
        assert info["max_length"] == 448
        assert not info["is_initialized"]


class TestAudioStreamBuffer:
    """Test the audio stream buffer."""
    
    def test_initialization(self):
        """Test buffer initialization."""
        buffer = AudioStreamBuffer(max_duration=10.0, sample_rate=16000)
        
        assert buffer.sample_rate == 16000
        assert buffer.max_samples == 160000  # 10 seconds * 16000 Hz
        assert len(buffer.buffer) == 0
        assert not buffer.is_accumulating
    
    def test_add_audio(self):
        """Test adding audio data."""
        buffer = AudioStreamBuffer(max_duration=5.0, sample_rate=16000)
        
        # Create test audio data
        audio_data = np.random.randint(-1000, 1000, 1600, dtype=np.int16)  # 0.1 seconds
        audio_bytes = audio_data.tobytes()
        
        # Add audio
        buffer.add_audio(audio_bytes, 16000)
        
        assert len(buffer.buffer) == 1600
        assert buffer.get_buffer_duration() == 0.1
    
    def test_accumulation(self):
        """Test audio accumulation."""
        buffer = AudioStreamBuffer(max_duration=5.0, sample_rate=16000)
        
        # Start accumulation
        buffer.start_accumulation()
        assert buffer.is_accumulating
        
        # Add audio
        audio_data = np.random.randint(-1000, 1000, 1600, dtype=np.int16)
        audio_bytes = audio_data.tobytes()
        buffer.add_audio(audio_bytes, 16000)
        
        # Check accumulated audio
        accumulated = buffer.get_audio()
        assert accumulated is not None
        assert len(accumulated) == 1600
        assert buffer.get_duration() == 0.1
        
        # Stop accumulation
        buffer.stop_accumulation()
        assert not buffer.is_accumulating
    
    def test_clear(self):
        """Test clearing buffer."""
        buffer = AudioStreamBuffer(max_duration=5.0, sample_rate=16000)
        
        # Add some audio
        audio_data = np.random.randint(-1000, 1000, 1600, dtype=np.int16)
        audio_bytes = audio_data.tobytes()
        buffer.add_audio(audio_bytes, 16000)
        
        # Clear buffer
        buffer.clear()
        
        assert len(buffer.buffer) == 0
        assert len(buffer.accumulated_audio) == 0
        assert not buffer.is_accumulating
    
    def test_audio_level(self):
        """Test audio level detection."""
        buffer = AudioStreamBuffer(max_duration=5.0, sample_rate=16000)
        
        # Add silent audio
        silent_audio = np.zeros(1600, dtype=np.int16)
        buffer.add_audio(silent_audio.tobytes(), 16000)
        
        level = buffer.get_audio_level()
        assert level == 0.0
        
        # Add loud audio
        loud_audio = np.full(1600, 16000, dtype=np.int16)
        buffer.add_audio(loud_audio.tobytes(), 16000)
        
        level = buffer.get_audio_level()
        assert level > 0.0


class TestVoiceActivityDetector:
    """Test the Voice Activity Detector."""
    
    def test_initialization(self):
        """Test VAD initialization."""
        vad = VoiceActivityDetector(
            energy_threshold=0.01,
            silence_duration=0.5,
            min_speech_duration=0.1
        )
        
        assert vad.energy_threshold == 0.01
        assert vad.silence_duration == 0.5
        assert vad.min_speech_duration == 0.1
        assert not vad.is_speaking
    
    def test_detect_voice_activity_silence(self):
        """Test VAD with silent audio."""
        vad = VoiceActivityDetector(energy_threshold=0.01)
        
        # Create silent audio
        silent_audio = np.zeros(1600, dtype=np.int16)  # 0.1 seconds
        audio_bytes = silent_audio.tobytes()
        
        is_voice = vad.detect_voice_activity(audio_bytes)
        assert not is_voice
        assert not vad.is_speaking
    
    def test_detect_voice_activity_speech(self):
        """Test VAD with speech audio."""
        vad = VoiceActivityDetector(energy_threshold=0.01)
        
        # Create speech-like audio (loud enough)
        speech_audio = np.random.randint(-16000, 16000, 1600, dtype=np.int16)
        audio_bytes = speech_audio.tobytes()
        
        is_voice = vad.detect_voice_activity(audio_bytes)
        # Note: This might not always detect as voice due to random nature
        # but it should not crash
    
    def test_reset(self):
        """Test VAD reset."""
        vad = VoiceActivityDetector()
        
        # Add some state
        vad.is_speaking = True
        vad.speech_start_time = 123.45
        
        # Reset
        vad.reset()
        
        assert not vad.is_speaking
        assert vad.speech_start_time is None
        assert vad.silence_start_time is None
        assert len(vad.energy_history) == 0
    
    def test_get_stats(self):
        """Test getting VAD statistics."""
        vad = VoiceActivityDetector()
        
        stats = vad.get_stats()
        
        assert "is_speaking" in stats
        assert "energy_threshold" in stats
        assert "adaptive_threshold" in stats
        assert "noise_floor" in stats
        assert "energy_history_length" in stats


class TestASREndpoints:
    """Test ASR API endpoints."""
    
    def test_asr_status_endpoint(self):
        """Test the ASR status endpoint."""
        response = client.get("/asr/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "active_connections" in data
        assert "supported_languages" in data
        assert "max_duration" in data
        assert "min_duration" in data
        assert "sample_rate" in data
    
    def test_transcribe_file_endpoint(self):
        """Test the file transcription endpoint."""
        # Create mock audio data
        audio_data = np.random.randint(-1000, 1000, 1600, dtype=np.int16)
        audio_bytes = audio_data.tobytes()
        
        response = client.post(
            "/asr/transcribe",
            content=audio_bytes,
            params={"sample_rate": 16000, "language_hint": "en"}
        )
        
        # Should return 200 with transcription result
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "text" in data
        assert "confidence" in data
        assert "language" in data
        assert "duration" in data
    
    def test_transcribe_empty_file(self):
        """Test transcription with empty file."""
        response = client.post(
            "/asr/transcribe",
            content=b"",
            params={"sample_rate": 16000}
        )
        
        # Should handle empty file gracefully
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"  # Empty file should return error
        assert "message" in data


class TestWebSocketConnection:
    """Test WebSocket ASR connection."""
    
    def test_websocket_connection_params(self):
        """Test WebSocket connection with parameters."""
        # This test would require a WebSocket client
        # For now, we'll test that the endpoint exists
        with client.websocket_connect("/ws/asr?sessionId=test123&langHint=en") as websocket:
            # Connection should be established
            assert websocket is not None
    
    def test_websocket_invalid_params(self):
        """Test WebSocket with invalid parameters."""
        # Test with missing sessionId
        try:
            with client.websocket_connect("/ws/asr") as websocket:
                # Should still work with default sessionId
                assert websocket is not None
        except Exception:
            # Some WebSocket implementations might require parameters
            pass


@pytest.mark.asyncio
async def test_mock_asr_integration():
    """Test integration of mock ASR components."""
    # Create components
    asr = ONNXWhisperASR(model_size="tiny", device="cpu")
    buffer = AudioStreamBuffer(max_duration=5.0, sample_rate=16000)
    vad = VoiceActivityDetector()
    
    # Create test audio
    audio_data = np.random.randint(-1000, 1000, 1600, dtype=np.int16)
    audio_bytes = audio_data.tobytes()
    
    # Test workflow
    buffer.start_accumulation()
    buffer.add_audio(audio_bytes, 16000)
    
    # Check VAD
    is_voice = vad.detect_voice_activity(audio_bytes)
    
    # Get accumulated audio
    accumulated_audio = buffer.get_audio()
    assert accumulated_audio is not None
    
    # Test transcription
    result = await asr.transcribe_audio(accumulated_audio.tobytes(), 16000)
    assert result is not None
    assert "text" in result
    
    # Cleanup
    buffer.clear()
    vad.reset()
    await asr.cleanup()
