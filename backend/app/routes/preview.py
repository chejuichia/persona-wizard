"""Preview generation endpoints."""

import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from ..core.models import PreviewRequest, PreviewResponse, ErrorResponse
from ..core.config import settings
from ..services.lipsync.sadtalker_adapter import SadTalkerAdapter
from ..services.lipsync.device import get_device

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/preview/generate", response_model=PreviewResponse)
async def generate_preview(request: PreviewRequest, background_tasks: BackgroundTasks):
    """Generate a preview video using sample assets."""
    try:
        # For S0, we'll use sample assets
        sample_image = settings.data_dir / "portraits" / "sample_face.png"
        sample_audio = settings.data_dir / "audio" / "hello_2s.wav"
        
        # Check if sample files exist
        if not sample_image.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"Sample image not found: {sample_image}"
            )
        
        if not sample_audio.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"Sample audio not found: {sample_audio}"
            )
        
        # Generate unique output filename
        output_filename = f"preview_{request.session_id}_{uuid.uuid4().hex[:8]}.mp4"
        output_path = settings.data_dir / "outputs" / output_filename
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize SadTalker adapter
        device = get_device()
        adapter = SadTalkerAdapter(device=device)
        
        # Generate video
        result = adapter.generate_video(
            image_path=sample_image,
            audio_path=sample_audio,
            output_path=output_path
        )
        
        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Video generation failed: {result.error}"
            )
        
        # Return response
        return PreviewResponse(
            url=f"/data/outputs/{output_filename}",
            duration_seconds=result.duration_seconds,
            size_px=result.size_px,
            fps=result.fps
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")


@router.get("/data/outputs/{filename}")
async def serve_output_file(filename: str):
    """Serve generated output files."""
    try:
        file_path = settings.data_dir / "outputs" / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            media_type="video/mp4",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve file {filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve file")


@router.get("/preview/status/{task_id}")
async def get_preview_status(task_id: str):
    """Get status of a preview generation task."""
    # For S0, we'll implement a simple status check
    # In later phases, this will integrate with a proper task queue
    try:
        # Check if output file exists
        output_dir = settings.data_dir / "outputs"
        matching_files = list(output_dir.glob(f"*{task_id}*"))
        
        if matching_files:
            file_path = matching_files[0]
            return {
                "task_id": task_id,
                "status": "completed",
                "url": f"/data/outputs/{file_path.name}",
                "created_at": file_path.stat().st_mtime
            }
        else:
            return {
                "task_id": task_id,
                "status": "not_found",
                "url": None
            }
            
    except Exception as e:
        logger.error(f"Failed to get preview status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get preview status")
