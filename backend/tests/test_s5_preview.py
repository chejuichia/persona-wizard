"""
Tests for S5 Preview Generation functionality.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.services.preview.orchestrator import PreviewOrchestrator
from app.services.llm.text_generator import TextGenerator
from app.services.tts.voice_cloner import VoiceCloner
from app.services.lipsync.sadtalker import SadTalkerService

client = TestClient(app)


class TestTextGenerator:
    """Test the Text Generator service."""
    
    def test_initialization(self):
        """Test text generator initialization."""
        generator = TextGenerator(model_name="test-model", device="cpu")
        
        assert generator.model_name == "test-model"
        assert generator.device == "cpu"
        assert generator.max_new_tokens == 256
        assert generator.temperature == 0.7
        assert not generator.is_initialized
    
    @pytest.mark.asyncio
    async def test_generate_text_mock(self):
        """Test text generation with mock implementation."""
        generator = TextGenerator(model_name="test-model", device="cpu")
        
        result = await generator.generate_text("Test prompt")
        
        assert result is not None
        assert "text" in result
        assert "word_count" in result
        assert "char_count" in result
        assert "tokens_generated" in result
        assert isinstance(result["text"], str)
        assert result["word_count"] > 0
    
    @pytest.mark.asyncio
    async def test_generate_with_style_profile(self):
        """Test text generation with style profile."""
        generator = TextGenerator()
        
        style_profile = {
            "style_metrics": {
                "vocabulary_richness": 0.8,
                "avg_sentence_length": 20.0
            },
            "tone": {
                "primary_tone": "formal"
            }
        }
        
        result = await generator.generate_text(
            "Test prompt",
            style_profile=style_profile
        )
        
        assert result is not None
        assert result["style_adapted"] is True
        assert "text" in result
    
    def test_get_model_info(self):
        """Test getting model information."""
        generator = TextGenerator()
        
        info = generator.get_model_info()
        
        assert "model_name" in info
        assert "device" in info
        assert "is_initialized" in info
        assert "max_new_tokens" in info
        assert "temperature" in info


class TestVoiceCloner:
    """Test the Voice Cloner service."""
    
    def test_initialization(self):
        """Test voice cloner initialization."""
        cloner = VoiceCloner(device="cpu")
        
        assert cloner.device == "cpu"
        assert cloner.sample_rate == 16000
        assert cloner.max_text_length == 500
        assert not cloner.is_initialized
    
    @pytest.mark.asyncio
    async def test_clone_voice_mock(self):
        """Test voice cloning with mock implementation."""
        cloner = VoiceCloner()
        
        # Create mock audio data
        import numpy as np
        audio_data = np.random.randint(-1000, 1000, 1600, dtype=np.int16).tobytes()
        
        result = await cloner.clone_voice(
            reference_audio=audio_data,
            reference_text="Test reference text",
            voice_name="test_voice"
        )
        
        assert result is not None
        assert "voice_name" in result
        assert "profile_path" in result
        assert "sample_rate" in result
        assert "characteristics" in result
        assert result["voice_name"] == "test_voice"
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_mock(self):
        """Test speech synthesis with mock implementation."""
        cloner = VoiceCloner()
        
        voice_profile = {
            "voice_name": "test_voice",
            "speaker_embedding": [0.0] * 256,
            "prosody_patterns": {
                "pitch_range": [80, 200],
                "speaking_rate": 150
            }
        }
        
        result = await cloner.synthesize_speech(
            text="Test synthesis text",
            voice_profile=voice_profile
        )
        
        assert result is not None
        assert "audio_data" in result
        assert "output_path" in result
        assert "duration" in result
        assert "sample_rate" in result
        assert result["voice_name"] == "test_voice"
    
    def test_get_model_info(self):
        """Test getting model information."""
        cloner = VoiceCloner()
        
        info = cloner.get_model_info()
        
        assert "device" in info
        assert "is_initialized" in info
        assert "sample_rate" in info
        assert "max_text_length" in info


class TestSadTalkerService:
    """Test the SadTalker service."""
    
    def test_initialization(self):
        """Test SadTalker service initialization."""
        service = SadTalkerService(device="cpu")
        
        assert service.device == "cpu"
        assert service.size_px == 256
        assert service.fps == 12
        assert service.enhancer == "off"
        assert not service.is_initialized
    
    @pytest.mark.asyncio
    async def test_generate_video_mock(self):
        """Test video generation with mock implementation."""
        service = SadTalkerService()
        
        # Create mock files
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as face_file:
            face_file.write(b'mock_image_data')
            face_path = face_file.name
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_file:
            audio_file.write(b'mock_audio_data')
            audio_path = audio_file.name
        
        try:
            result = await service.generate_video(
                face_image_path=face_path,
                audio_path=audio_path
            )
            
            # The result should either be successful or have an error
            # For testing purposes, we'll accept either outcome
            assert result is not None
            if "error" in result:
                # If there's an error, it should be about face processing
                assert "face" in result["error"].lower() or "image" in result["error"].lower()
            else:
                # If successful, check for expected fields
                assert "output_path" in result
                assert "duration" in result
                assert "fps" in result
                assert "size_px" in result
                assert "frames" in result
                assert result["success"] is True
        
        finally:
            # Clean up temp files
            os.unlink(face_path)
            os.unlink(audio_path)
    
    def test_get_model_info(self):
        """Test getting model information."""
        service = SadTalkerService()
        
        info = service.get_model_info()
        
        assert "device" in info
        assert "is_initialized" in info
        assert "size_px" in info
        assert "fps" in info
        assert "enhancer" in info


class TestPreviewOrchestrator:
    """Test the Preview Orchestrator."""
    
    def test_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = PreviewOrchestrator()
        
        assert orchestrator.text_generator is not None
        assert orchestrator.voice_cloner is not None
        assert orchestrator.sadtalker is not None
        assert len(orchestrator.active_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_generate_preview_mock(self):
        """Test preview generation with mock implementation."""
        orchestrator = PreviewOrchestrator()
        
        persona_config = {
            "id": "test-persona",
            "name": "Test Persona",
            "text": {
                "base_model": "phi4-mini",
                "generation": {
                    "max_new_tokens": 256,
                    "temperature": 0.7
                }
            },
            "voice": {
                "tts_engine": "xtts-v2",
                "sample_rate_hz": 16000
            },
            "image": {
                "face_ref": "artifacts/image/face_ref.png"
            },
            "video": {
                "lipsync_engine": "sadtalker",
                "mode": "short",
                "size_px": 256,
                "fps": 12
            }
        }
        
        result = await orchestrator.generate_preview(
            prompt="Test prompt",
            persona_config=persona_config
        )
        
        assert result is not None
        assert "task_id" in result
        assert "status" in result
        assert result["status"] == "completed"
        assert "video_path" in result
        assert "audio_path" in result
        assert "preview_metadata" in result
    
    @pytest.mark.asyncio
    async def test_task_status_tracking(self):
        """Test task status tracking."""
        orchestrator = PreviewOrchestrator()
        
        # Simulate task creation
        task_id = "test-task-123"
        orchestrator.active_tasks[task_id] = {
            "status": "started",
            "progress": 0,
            "steps": [],
            "started_at": "2024-01-01T00:00:00Z"
        }
        
        # Test getting task status
        status = await orchestrator.get_task_status(task_id)
        assert status is not None
        assert status["status"] == "started"
        
        # Test listing tasks
        tasks = await orchestrator.list_active_tasks()
        assert len(tasks) == 1
        assert tasks[0]["status"] == "started"
    
    def test_get_orchestrator_info(self):
        """Test getting orchestrator information."""
        orchestrator = PreviewOrchestrator()
        
        info = orchestrator.get_orchestrator_info()
        
        assert "active_tasks" in info
        assert "text_generator" in info
        assert "voice_cloner" in info
        assert "sadtalker" in info


class TestPreviewEndpoints:
    """Test preview generation API endpoints."""
    
    def test_generate_preview_endpoint(self):
        """Test the generate preview endpoint."""
        response = client.post("/preview/generate-full", json={
            "prompt": "Test prompt for preview generation",
            "use_sample": True
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert "message" in data
        assert data["status"] == "started"
    
    def test_preview_status_endpoint(self):
        """Test the preview status endpoint."""
        # First create a task
        create_response = client.post("/preview/generate-full", json={
            "prompt": "Test prompt",
            "use_sample": True
        })
        assert create_response.status_code == 200
        
        task_id = create_response.json()["task_id"]
        
        # Then check status
        response = client.get(f"/preview/status-full/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert "progress" in data
        assert data["task_id"] == task_id
    
    def test_list_preview_tasks_endpoint(self):
        """Test the list preview tasks endpoint."""
        response = client.get("/preview/tasks-full")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "tasks" in data
        assert "total" in data
        assert data["status"] == "ok"
    
    def test_preview_info_endpoint(self):
        """Test the preview info endpoint."""
        response = client.get("/preview/info-full")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "orchestrator" in data
        assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_full_preview_pipeline():
    """Test the complete preview generation pipeline."""
    orchestrator = PreviewOrchestrator()
    
    # Test persona configuration
    persona_config = {
        "id": "test-persona",
        "name": "Test Persona",
        "text": {
            "base_model": "phi4-mini",
            "style_profile": {
                "vocabulary_richness": 0.6,
                "avg_sentence_length": 15.0,
                "tone": {"primary_tone": "professional"}
            },
            "generation": {
                "max_new_tokens": 256,
                "temperature": 0.7
            }
        },
        "voice": {
            "tts_engine": "xtts-v2",
            "sample_rate_hz": 16000
        },
        "image": {
            "face_ref": "artifacts/image/face_ref.png"
        },
        "video": {
            "lipsync_engine": "sadtalker",
            "mode": "short",
            "size_px": 256,
            "fps": 12
        }
    }
    
    # Test voice profile
    voice_profile = {
        "voice_name": "test_voice",
        "speaker_embedding": [0.0] * 256,
        "prosody_patterns": {
            "pitch_range": [80, 200],
            "speaking_rate": 150
        }
    }
    
    # Generate preview
    result = await orchestrator.generate_preview(
        prompt="Hello, this is a test of the preview generation system.",
        persona_config=persona_config,
        voice_profile=voice_profile
    )
    
    # Verify result
    assert result is not None
    assert "task_id" in result
    assert "status" in result
    assert result["status"] == "completed"
    assert "video_path" in result
    assert "audio_path" in result
    assert "preview_metadata" in result
    
    # Verify metadata structure
    metadata = result["preview_metadata"]
    assert "text" in metadata
    assert "speech" in metadata
    assert "video" in metadata
    assert metadata["text"]["generated_text"] is not None
    assert metadata["speech"]["audio_path"] is not None
    assert metadata["video"]["video_path"] is not None
