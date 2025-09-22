"""Image upload and processing endpoints."""

import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse

from ..core.config import settings
from ..core.models import ErrorResponse
from ..services.image.face_prep import prepare_face_image, create_sample_face

logger = logging.getLogger(__name__)
router = APIRouter()

# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/wizard/image/upload")
async def upload_image(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    target_size: int = Form(512)
):
    """Upload and process image for face preparation."""
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
        
        # Create image ID
        image_id = str(uuid.uuid4())
        
        # Create upload directory
        upload_dir = settings.data_dir / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save original image
        original_filename = f"{image_id}_original{file_extension}"
        original_path = upload_dir / original_filename
        with open(original_path, 'wb') as f:
            f.write(content)
        
        # Create artifacts directory
        image_dir = settings.artifacts_dir / "image"
        image_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare face
        face_filename = f"{image_id}_face_ref.png"
        face_path = image_dir / face_filename
        
        result = prepare_face_image(
            input_path=original_path,
            output_path=face_path,
            target_size=target_size
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Face preparation failed: {result.get('error', 'Unknown error')}"
            )
        
        logger.info(f"Image uploaded and processed successfully: {image_id}")
        
        return JSONResponse(content={
            "status": "ok",
            "image_id": image_id,
            "session_id": session_id,
            "face_detected": result["face_detected"],
            "original_size": result["original_size"],
            "output_size": result["output_size"],
            "face_info": {
                "method": result.get("face_info", {}).get("method", "unknown"),
                "confidence": result.get("face_info", {}).get("confidence", 0.0),
                "position": {
                    "x": result.get("face_info", {}).get("x", 0),
                    "y": result.get("face_info", {}).get("y", 0),
                    "width": result.get("face_info", {}).get("width", 0),
                    "height": result.get("face_info", {}).get("height", 0)
                }
            },
            "files": {
                "original": str(original_path.relative_to(settings.data_dir)),
                "face_ref": str(face_path.relative_to(settings.artifacts_dir))
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        raise HTTPException(status_code=500, detail="Image upload failed")


@router.get("/wizard/image/{image_id}/face")
async def get_face_image(image_id: str):
    """Get prepared face image."""
    try:
        face_path = settings.artifacts_dir / "image" / f"{image_id}_face_ref.png"
        
        if not face_path.exists():
            raise HTTPException(status_code=404, detail="Face image not found")
        
        return FileResponse(
            path=str(face_path),
            media_type="image/png",
            filename=f"{image_id}_face_ref.png"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get face image: {e}")
        raise HTTPException(status_code=500, detail="Failed to get face image")


@router.get("/wizard/image/{image_id}/original")
async def get_original_image(image_id: str):
    """Get original uploaded image."""
    try:
        # Try to find the original file
        upload_dir = settings.data_dir / "uploads"
        original_files = list(upload_dir.glob(f"{image_id}_original.*"))
        
        if not original_files:
            raise HTTPException(status_code=404, detail="Original image not found")
        
        original_path = original_files[0]
        
        # Determine media type
        file_extension = original_path.suffix.lower()
        media_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.webp': 'image/webp'
        }
        media_type = media_type_map.get(file_extension, 'application/octet-stream')
        
        return FileResponse(
            path=str(original_path),
            media_type=media_type,
            filename=original_path.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get original image: {e}")
        raise HTTPException(status_code=500, detail="Failed to get original image")


@router.get("/wizard/image/{image_id}/info")
async def get_image_info(image_id: str):
    """Get image processing information."""
    try:
        face_path = settings.artifacts_dir / "image" / f"{image_id}_face_ref.png"
        
        if not face_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Get file info
        face_stat = face_path.stat()
        
        # Try to get original file info
        upload_dir = settings.data_dir / "uploads"
        original_files = list(upload_dir.glob(f"{image_id}_original.*"))
        original_info = None
        
        if original_files:
            original_stat = original_files[0].stat()
            original_info = {
                "filename": original_files[0].name,
                "size_bytes": original_stat.st_size,
                "created_at": original_stat.st_ctime
            }
        
        return JSONResponse(content={
            "status": "ok",
            "image_id": image_id,
            "face_image": {
                "filename": face_path.name,
                "size_bytes": face_stat.st_size,
                "created_at": face_stat.st_ctime
            },
            "original_image": original_info
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get image info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get image info")


@router.delete("/wizard/image/{image_id}")
async def delete_image(image_id: str):
    """Delete uploaded image and its artifacts."""
    try:
        deleted_files = []
        
        # Delete face image
        face_path = settings.artifacts_dir / "image" / f"{image_id}_face_ref.png"
        if face_path.exists():
            face_path.unlink()
            deleted_files.append(str(face_path.name))
        
        # Delete original image
        upload_dir = settings.data_dir / "uploads"
        original_files = list(upload_dir.glob(f"{image_id}_original.*"))
        for original_file in original_files:
            original_file.unlink()
            deleted_files.append(original_file.name)
        
        if not deleted_files:
            raise HTTPException(status_code=404, detail="Image not found")
        
        logger.info(f"Deleted image {image_id}: {deleted_files}")
        
        return JSONResponse(content={
            "status": "ok",
            "image_id": image_id,
            "deleted_files": deleted_files
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete image: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete image")


@router.post("/wizard/image/sample")
async def create_sample_image(
    session_id: Optional[str] = Form(None),
    target_size: int = Form(512)
):
    """Create a sample face image for testing."""
    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Create image ID
        image_id = str(uuid.uuid4())
        
        # Create artifacts directory
        image_dir = settings.artifacts_dir / "image"
        image_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample face
        face_filename = f"{image_id}_face_ref.png"
        face_path = image_dir / face_filename
        
        create_sample_face(face_path, target_size)
        
        logger.info(f"Sample image created: {image_id}")
        
        return JSONResponse(content={
            "status": "ok",
            "image_id": image_id,
            "session_id": session_id,
            "face_detected": True,  # Sample face is always "detected"
            "output_size": (target_size, target_size),
            "files": {
                "face_ref": str(face_path.relative_to(settings.artifacts_dir))
            }
        })
        
    except Exception as e:
        logger.error(f"Sample image creation failed: {e}")
        raise HTTPException(status_code=500, detail="Sample image creation failed")
