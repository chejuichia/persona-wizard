"""
Wizard Voice Routes

Handles voice recording upload and processing for voice cloning.
"""

import uuid
import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse

from ..services.tts.voice_cloner import VoiceCloner
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/wizard/voice", tags=["wizard-voice"])

# Initialize voice cloner
voice_cloner = VoiceCloner()

# Supported audio formats
SUPPORTED_FORMATS = ['.wav', '.mp3', '.m4a', '.webm', '.ogg']
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/upload")
async def upload_voice(
    file: UploadFile = File(...),
    reference_text: str = Form(..., min_length=10, max_length=1000),
    session_id: Optional[str] = Form(None)
):
    """Upload voice recording for voice cloning."""
    try:
        # Validate file type
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format. Supported: {', '.join(SUPPORTED_FORMATS)}"
            )
        
        # Validate file size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Create voice ID
        voice_id = str(uuid.uuid4())
        
        # Create voice directory
        voice_dir = settings.artifacts_dir / "voice"
        voice_dir.mkdir(parents=True, exist_ok=True)
        
        # Save original audio
        original_filename = f"{voice_id}_original{file_extension}"
        original_path = voice_dir / original_filename
        with open(original_path, 'wb') as f:
            f.write(content)
        
        # Process voice for cloning
        voice_name = f"voice_{voice_id}"
        clone_result = await voice_cloner.clone_voice(
            reference_audio=content,
            reference_text=reference_text,
            voice_name=voice_name
        )
        
        if "error" in clone_result:
            raise HTTPException(
                status_code=400,
                detail=f"Voice cloning failed: {clone_result['error']}"
            )
        
        # Save voice profile
        profile_filename = f"{voice_id}_xtts_speaker.json"
        profile_path = voice_dir / profile_filename
        with open(profile_path, 'w') as f:
            json.dump(clone_result["characteristics"], f, indent=2)
        
        # Save voice metadata
        metadata_filename = f"{voice_id}_metadata.json"
        metadata_path = voice_dir / metadata_filename
        metadata = {
            "voice_id": voice_id,
            "voice_name": voice_name,
            "reference_text": reference_text,
            "duration": clone_result["duration"],
            "sample_rate": clone_result["sample_rate"],
            "original_file": original_filename,
            "profile_file": profile_filename,
            "created_at": clone_result["characteristics"]["metadata"]["created_at"]
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Voice uploaded and processed successfully: {voice_id}")
        
        return JSONResponse(content={
            "status": "ok",
            "voice_id": voice_id,
            "session_id": session_id,
            "voice_name": voice_name,
            "duration": clone_result["duration"],
            "sample_rate": clone_result["sample_rate"],
            "files": {
                "original": str(original_path.relative_to(settings.artifacts_dir)),
                "profile": str(profile_path.relative_to(settings.artifacts_dir)),
                "metadata": str(metadata_path.relative_to(settings.artifacts_dir))
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice upload failed: {str(e)}")


@router.post("/clone")
async def clone_voice_from_recording(
    audio_data: bytes = File(...),
    reference_text: str = Form(..., min_length=10, max_length=1000),
    session_id: Optional[str] = Form(None)
):
    """Clone voice from raw audio data (e.g., from WebSocket recording)."""
    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Create voice ID
        voice_id = str(uuid.uuid4())
        
        # Create voice directory
        voice_dir = settings.artifacts_dir / "voice"
        voice_dir.mkdir(parents=True, exist_ok=True)
        
        # Save original audio
        original_filename = f"{voice_id}_original.webm"
        original_path = voice_dir / original_filename
        with open(original_path, 'wb') as f:
            f.write(audio_data)
        
        # Process voice for cloning
        voice_name = f"voice_{voice_id}"
        clone_result = await voice_cloner.clone_voice(
            reference_audio=audio_data,
            reference_text=reference_text,
            voice_name=voice_name
        )
        
        if "error" in clone_result:
            raise HTTPException(
                status_code=400,
                detail=f"Voice cloning failed: {clone_result['error']}"
            )
        
        # Save voice profile
        profile_filename = f"{voice_id}_xtts_speaker.json"
        profile_path = voice_dir / profile_filename
        with open(profile_path, 'w') as f:
            json.dump(clone_result["characteristics"], f, indent=2)
        
        # Save voice metadata
        metadata_filename = f"{voice_id}_metadata.json"
        metadata_path = voice_dir / metadata_filename
        metadata = {
            "voice_id": voice_id,
            "voice_name": voice_name,
            "reference_text": reference_text,
            "duration": clone_result["duration"],
            "sample_rate": clone_result["sample_rate"],
            "original_file": original_filename,
            "profile_file": profile_filename,
            "created_at": clone_result["characteristics"]["metadata"]["created_at"]
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Voice cloned successfully: {voice_id}")
        
        return JSONResponse(content={
            "status": "ok",
            "voice_id": voice_id,
            "session_id": session_id,
            "voice_name": voice_name,
            "duration": clone_result["duration"],
            "sample_rate": clone_result["sample_rate"],
            "files": {
                "original": str(original_path.relative_to(settings.artifacts_dir)),
                "profile": str(profile_path.relative_to(settings.artifacts_dir)),
                "metadata": str(metadata_path.relative_to(settings.artifacts_dir))
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice cloning failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice cloning failed: {str(e)}")


@router.get("/{voice_id}/info")
async def get_voice_info(voice_id: str):
    """Get information about a voice recording."""
    try:
        voice_dir = settings.artifacts_dir / "voice"
        metadata_path = voice_dir / f"{voice_id}_metadata.json"
        
        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail="Voice not found")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return JSONResponse(content={
            "status": "ok",
            "voice_id": voice_id,
            "metadata": metadata
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get voice info for {voice_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get voice info: {str(e)}")


@router.delete("/{voice_id}")
async def delete_voice(voice_id: str):
    """Delete a voice recording and its artifacts."""
    try:
        voice_dir = settings.artifacts_dir / "voice"
        
        # Find all files for this voice_id
        files_to_delete = list(voice_dir.glob(f"{voice_id}_*"))
        
        if not files_to_delete:
            raise HTTPException(status_code=404, detail="Voice not found")
        
        # Delete all files
        for file_path in files_to_delete:
            file_path.unlink()
        
        logger.info(f"Deleted voice {voice_id} and {len(files_to_delete)} files")
        
        return JSONResponse(content={
            "status": "ok",
            "voice_id": voice_id,
            "files_deleted": len(files_to_delete)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete voice {voice_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete voice: {str(e)}")
