"""
Artifacts API Routes

Provides endpoints for managing and retrieving previously uploaded artifacts.
"""

from typing import Dict, List, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..services.artifacts.manager import ArtifactManager, ArtifactInfo
from ..core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/artifacts", tags=["artifacts"])

# Initialize artifact manager
artifact_manager = ArtifactManager()


class ArtifactResponse(BaseModel):
    """Response model for artifact information."""
    id: str
    type: str
    name: str
    created_at: str
    file_path: str
    metadata: Dict
    size: Optional[int] = None
    duration: Optional[float] = None
    dimensions: Optional[List[int]] = None


class ArtifactsListResponse(BaseModel):
    """Response model for artifacts list."""
    artifacts: Dict[str, List[ArtifactResponse]]
    stats: Dict


@router.get("/", response_model=ArtifactsListResponse)
async def get_all_artifacts():
    """Get all previously uploaded artifacts grouped by type."""
    try:
        all_artifacts = artifact_manager.get_all_artifacts()
        stats = artifact_manager.get_artifact_stats()
        
        # Convert ArtifactInfo to ArtifactResponse
        artifacts_response = {}
        for artifact_type, artifacts in all_artifacts.items():
            artifacts_response[artifact_type] = [
                ArtifactResponse(
                    id=artifact.id,
                    type=artifact.type,
                    name=artifact.name,
                    created_at=artifact.created_at,
                    file_path=artifact.file_path,
                    metadata=artifact.metadata,
                    size=artifact.size,
                    duration=artifact.duration,
                    dimensions=list(artifact.dimensions) if artifact.dimensions else None
                )
                for artifact in artifacts
            ]
        
        return ArtifactsListResponse(
            artifacts=artifacts_response,
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"Failed to get all artifacts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve artifacts: {str(e)}")


@router.get("/audio", response_model=List[ArtifactResponse])
async def get_audio_artifacts():
    """Get all previously uploaded audio artifacts."""
    try:
        artifacts = artifact_manager.get_audio_artifacts()
        
        return [
            ArtifactResponse(
                id=artifact.id,
                type=artifact.type,
                name=artifact.name,
                created_at=artifact.created_at,
                file_path=artifact.file_path,
                metadata=artifact.metadata,
                size=artifact.size,
                duration=artifact.duration,
                dimensions=list(artifact.dimensions) if artifact.dimensions else None
            )
            for artifact in artifacts
        ]
        
    except Exception as e:
        logger.error(f"Failed to get audio artifacts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audio artifacts: {str(e)}")


@router.get("/text", response_model=List[ArtifactResponse])
async def get_text_artifacts():
    """Get all previously uploaded text artifacts."""
    try:
        artifacts = artifact_manager.get_text_artifacts()
        
        return [
            ArtifactResponse(
                id=artifact.id,
                type=artifact.type,
                name=artifact.name,
                created_at=artifact.created_at,
                file_path=artifact.file_path,
                metadata=artifact.metadata,
                size=artifact.size,
                duration=artifact.duration,
                dimensions=list(artifact.dimensions) if artifact.dimensions else None
            )
            for artifact in artifacts
        ]
        
    except Exception as e:
        logger.error(f"Failed to get text artifacts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve text artifacts: {str(e)}")


@router.get("/image", response_model=List[ArtifactResponse])
async def get_image_artifacts():
    """Get all previously uploaded image artifacts."""
    try:
        artifacts = artifact_manager.get_image_artifacts()
        
        return [
            ArtifactResponse(
                id=artifact.id,
                type=artifact.type,
                name=artifact.name,
                created_at=artifact.created_at,
                file_path=artifact.file_path,
                metadata=artifact.metadata,
                size=artifact.size,
                duration=artifact.duration,
                dimensions=list(artifact.dimensions) if artifact.dimensions else None
            )
            for artifact in artifacts
        ]
        
    except Exception as e:
        logger.error(f"Failed to get image artifacts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve image artifacts: {str(e)}")


@router.get("/{artifact_type}/{artifact_id}")
async def get_artifact_file(artifact_type: str, artifact_id: str):
    """Get a specific artifact file by type and ID."""
    try:
        artifact = artifact_manager.get_artifact_by_id(artifact_id, artifact_type)
        
        if not artifact:
            raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} of type {artifact_type} not found")
        
        # Check if file exists
        file_path = Path(artifact.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Artifact file not found")
        
        # Determine media type based on file extension
        media_type = "application/octet-stream"
        if file_path.suffix.lower() in ['.txt', '.json']:
            media_type = "text/plain"
        elif file_path.suffix.lower() in ['.wav', '.mp3', '.webm']:
            media_type = "audio/wav" if file_path.suffix.lower() == '.wav' else "audio/webm"
        elif file_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            media_type = f"image/{file_path.suffix.lower()[1:]}"
        
        # Return the file content
        from fastapi.responses import FileResponse
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=artifact.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get artifact file {artifact_id} of type {artifact_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve artifact file: {str(e)}")


@router.delete("/{artifact_type}/{artifact_id}")
async def delete_artifact(artifact_type: str, artifact_id: str):
    """Delete a specific artifact by type and ID."""
    try:
        success = artifact_manager.delete_artifact(artifact_id, artifact_type)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} of type {artifact_type} not found")
        
        return {"message": f"Artifact {artifact_id} of type {artifact_type} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete artifact {artifact_id} of type {artifact_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete artifact: {str(e)}")


@router.get("/stats")
async def get_artifact_stats():
    """Get statistics about stored artifacts."""
    try:
        stats = artifact_manager.get_artifact_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get artifact stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve artifact stats: {str(e)}")
