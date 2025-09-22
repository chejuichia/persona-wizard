"""
Preview Generation Routes

Handles preview video generation using the complete pipeline:
LLM → TTS → SadTalker → MP4 output
"""

import asyncio
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..services.preview.orchestrator import orchestrator
from ..services.bundle.builder import BundleBuilder
from ..core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()
bundle_builder = BundleBuilder()


class PreviewRequest(BaseModel):
    prompt: str
    persona_id: Optional[str] = None
    text_id: Optional[str] = None
    image_id: Optional[str] = None
    voice_id: Optional[str] = None
    use_sample: bool = False


class PreviewResponse(BaseModel):
    task_id: str
    status: str
    message: str
    progress: int = 0


class PreviewStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    current_step: Optional[str] = None
    message: Optional[str] = None
    video_path: Optional[str] = None
    audio_path: Optional[str] = None
    error: Optional[str] = None


@router.post("/preview/generate-full", response_model=PreviewResponse)
async def generate_preview(request: PreviewRequest, background_tasks: BackgroundTasks):
    """
    Generate a preview video using the complete pipeline.
    
    This endpoint starts the preview generation process in the background.
    Use the status endpoint to check progress and get results.
    """
    try:
        logger.info(f"Starting preview generation for prompt: {request.prompt[:50]}...")
        
        # Get persona configuration
        persona_config = await _get_persona_config(
            request.persona_id,
            request.text_id,
            request.image_id,
            request.voice_id,
            request.use_sample
        )
        
        # Get voice profile if available
        voice_profile = None
        if request.voice_id:
            voice_profile = await _get_voice_profile(request.voice_id)
        
        # Get face image path if available
        face_image_path = None
        if request.image_id:
            face_image_path = await _get_face_image_path(request.image_id)
        
        # Generate a task ID first
        task_id = str(uuid.uuid4())
        
        # Start preview generation in background
        task = asyncio.create_task(
            orchestrator.generate_preview_with_id(
                task_id=task_id,
                prompt=request.prompt,
                persona_config=persona_config,
                voice_profile=voice_profile,
                face_image_path=face_image_path
            )
        )
        
        logger.info(f"Preview generation task started: {task_id}")
        
        return PreviewResponse(
            task_id=task_id,
            status="started",
            message="Preview generation started",
            progress=0
        )
        
    except Exception as e:
        logger.error(f"Failed to start preview generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start preview generation: {str(e)}")


@router.get("/preview/status-full/{task_id}", response_model=PreviewStatusResponse)
async def get_preview_status(task_id: str):
    """
    Get the status of a preview generation task.
    
    Returns current progress, status, and results when available.
    """
    try:
        task_status = await orchestrator.get_task_status(task_id)
        
        if not task_status:
            raise HTTPException(status_code=404, detail="Task not found")
        
        response_data = {
            "task_id": task_id,
            "status": task_status["status"],
            "progress": task_status.get("progress", 0),
            "current_step": task_status.get("current_step"),
            "message": task_status.get("steps", [{}])[-1].get("message") if task_status.get("steps") else None
        }
        
        # Add result paths if completed
        if task_status["status"] == "completed":
            preview_metadata = task_status.get("preview_metadata", {})
            response_data.update({
                "video_path": preview_metadata.get("video", {}).get("video_path"),
                "audio_path": preview_metadata.get("speech", {}).get("audio_path")
            })
        elif task_status["status"] == "failed":
            response_data["error"] = task_status.get("error")
        
        return PreviewStatusResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get preview status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get preview status: {str(e)}")


@router.get("/preview/tasks-full")
async def list_preview_tasks():
    """List all active preview generation tasks."""
    try:
        tasks = await orchestrator.list_active_tasks()
        return {
            "status": "ok",
            "tasks": tasks,
            "total": len(tasks)
        }
    except Exception as e:
        logger.error(f"Failed to list preview tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list preview tasks: {str(e)}")


@router.delete("/preview/tasks-full/{task_id}")
async def cancel_preview_task(task_id: str):
    """Cancel a preview generation task."""
    try:
        success = await orchestrator.cancel_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "status": "ok",
            "message": f"Task {task_id} cancelled successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel preview task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel preview task: {str(e)}")


@router.get("/preview/info-full")
async def get_preview_info():
    """Get preview generation system information."""
    try:
        info = orchestrator.get_orchestrator_info()
        return {
            "status": "ok",
            "orchestrator": info
        }
    except Exception as e:
        logger.error(f"Failed to get preview info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get preview info: {str(e)}")


async def _get_persona_config(
    persona_id: Optional[str],
    text_id: Optional[str],
    image_id: Optional[str],
    voice_id: Optional[str],
    use_sample: bool
) -> Dict[str, Any]:
    """Get persona configuration from uploaded samples or use defaults."""
    
    if use_sample:
        # Use sample configuration
        return {
            "id": "sample-persona",
            "name": "Sample Persona",
            "text": {
                "base_model": "phi4-mini",
                "style": {
                    "mode": "profile",
                    "adapter_path": "artifacts/text/sample_style.json"
                },
                "generation": {
                    "max_new_tokens": 256,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            },
            "voice": {
                "tts_engine": "xtts-v2",
                "speaker_profile": "artifacts/voice/sample_speaker.pth",
                "sample_rate_hz": 16000,
                "metadata": {
                    "language": "en",
                    "speaking_rate": "medium",
                    "pitch": "neutral",
                    "energy": "calm"
                }
            },
            "image": {
                "face_ref": "artifacts/image/sample_face.png"
            },
            "video": {
                "lipsync_engine": "sadtalker",
                "mode": "short",
                "size_px": 256,
                "fps": 12,
                "enhancer": "off"
            }
        }
    
    # Build configuration from uploaded samples
    config = {
        "id": persona_id or "custom-persona",
        "name": "Custom Persona",
        "text": {
            "base_model": "phi4-mini",
            "style": {
                "mode": "profile",
                "adapter_path": "artifacts/text/style_profile.json"
            },
            "generation": {
                "max_new_tokens": 256,
                "temperature": 0.7,
                "top_p": 0.9
            }
        },
        "voice": {
            "tts_engine": "xtts-v2",
            "speaker_profile": "artifacts/voice/xtts_speaker.pth",
            "sample_rate_hz": 16000,
            "metadata": {
                "language": "en",
                "speaking_rate": "medium",
                "pitch": "neutral",
                "energy": "calm"
            }
        },
        "image": {
            "face_ref": "artifacts/image/face_ref.png"
        },
        "video": {
            "lipsync_engine": "sadtalker",
            "mode": "short",
            "size_px": 256,
            "fps": 12,
            "enhancer": "off"
        }
    }
    
    # Add style profile if text_id provided
    if text_id:
        # TODO: Load actual style profile from text_id
        config["text"]["style_profile"] = {
            "vocabulary_richness": 0.6,
            "avg_sentence_length": 15.0,
            "tone": {
                "primary_tone": "professional"
            }
        }
    
    return config


async def _get_voice_profile(voice_id: str) -> Optional[Dict[str, Any]]:
    """Get voice profile from voice_id."""
    # TODO: Load actual voice profile from voice_id
    # For now, return a mock profile
    return {
        "voice_name": f"voice_{voice_id}",
        "speaker_embedding": [0.0] * 256,
        "prosody_patterns": {
            "pitch_range": [80, 200],
            "speaking_rate": 150,
            "pitch_mean": 140,
            "energy_mean": 0.5
        },
        "acoustic_features": {
            "mfcc_mean": [0.0] * 13,
            "spectral_centroid": 2000.0,
            "zero_crossing_rate": 0.1
        }
    }


async def _get_face_image_path(image_id: str) -> Optional[str]:
    """Get face image path from image_id."""
    # TODO: Get actual face image path from image_id
    # For now, return a placeholder
    return "artifacts/image/face_ref.png"
