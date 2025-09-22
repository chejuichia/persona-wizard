"""Text upload and processing endpoints."""

import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse

from ..core.config import settings
from ..core.models import ErrorResponse
from ..services.text.style_profile import create_style_profile

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/wizard/text/upload")
async def upload_text(
    text: str = Form(..., min_length=10, max_length=100000),
    session_id: Optional[str] = Form(None)
):
    """Upload and process text for style analysis."""
    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Create text ID
        text_id = str(uuid.uuid4())
        
        # Create output directory
        text_dir = settings.artifacts_dir / "text"
        text_dir.mkdir(parents=True, exist_ok=True)
        
        # Save raw text
        raw_text_path = text_dir / f"{text_id}_raw.txt"
        with open(raw_text_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Create style profile
        profile_path = text_dir / f"{text_id}_style_profile.json"
        profile = create_style_profile(text, profile_path)
        
        # Calculate token count (rough estimate)
        token_count = len(text.split()) * 1.3  # Rough token estimation
        
        logger.info(f"Text uploaded successfully: {text_id}")
        
        return JSONResponse(content={
            "status": "ok",
            "text_id": text_id,
            "session_id": session_id,
            "token_count": int(token_count),
            "word_count": profile["metadata"]["word_count"],
            "character_count": profile["metadata"]["character_count"],
            "style_profile": {
                "vocabulary_richness": profile["style_metrics"]["vocabulary_richness"],
                "avg_sentence_length": profile["style_metrics"]["avg_sentence_length"],
                "reading_ease": profile["style_metrics"]["reading_ease"],
                "tone": profile["tone"]
            },
            "files": {
                "raw_text": str(raw_text_path.relative_to(settings.artifacts_dir)),
                "style_profile": str(profile_path.relative_to(settings.artifacts_dir))
            }
        })
        
    except ValueError as e:
        logger.warning(f"Text upload validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Text upload failed: {e}")
        raise HTTPException(status_code=500, detail="Text upload failed")


@router.post("/wizard/text/upload-file")
async def upload_text_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """Upload text file for style analysis."""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('text/'):
            raise HTTPException(status_code=400, detail="File must be a text file")
        
        # Read file content
        content = await file.read()
        text = content.decode('utf-8')
        
        if len(text) < 10:
            raise HTTPException(status_code=400, detail="Text file must contain at least 10 characters")
        
        if len(text) > 100000:
            raise HTTPException(status_code=400, detail="Text file too large (max 100,000 characters)")
        
        # Process the text
        return await upload_text(text=text, session_id=session_id)
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be valid UTF-8 text")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text file upload failed: {e}")
        raise HTTPException(status_code=500, detail="Text file upload failed")


@router.get("/wizard/text/{text_id}/profile")
async def get_text_profile(text_id: str):
    """Get style profile for uploaded text."""
    try:
        profile_path = settings.artifacts_dir / "text" / f"{text_id}_style_profile.json"
        
        if not profile_path.exists():
            raise HTTPException(status_code=404, detail="Text profile not found")
        
        import json
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        
        return JSONResponse(content={
            "status": "ok",
            "text_id": text_id,
            "profile": profile
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get text profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to get text profile")


@router.get("/wizard/text/{text_id}/raw")
async def get_raw_text(text_id: str):
    """Get raw text content."""
    try:
        text_path = settings.artifacts_dir / "text" / f"{text_id}_raw.txt"
        
        if not text_path.exists():
            raise HTTPException(status_code=404, detail="Text not found")
        
        with open(text_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        return JSONResponse(content={
            "status": "ok",
            "text_id": text_id,
            "text": text_content
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get raw text: {e}")
        raise HTTPException(status_code=500, detail="Failed to get raw text")


@router.delete("/wizard/text/{text_id}")
async def delete_text(text_id: str):
    """Delete uploaded text and its artifacts."""
    try:
        text_dir = settings.artifacts_dir / "text"
        
        # Find and delete all files for this text_id
        deleted_files = []
        for pattern in [f"{text_id}_*"]:
            for file_path in text_dir.glob(pattern):
                file_path.unlink()
                deleted_files.append(str(file_path.name))
        
        if not deleted_files:
            raise HTTPException(status_code=404, detail="Text not found")
        
        logger.info(f"Deleted text {text_id}: {deleted_files}")
        
        return JSONResponse(content={
            "status": "ok",
            "text_id": text_id,
            "deleted_files": deleted_files
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete text: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete text")
