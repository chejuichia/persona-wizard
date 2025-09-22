"""Pydantic models for API requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""
    ok: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "0.1.0"


class PreviewRequest(BaseModel):
    """Request to generate a preview video."""
    session_id: UUID = Field(default_factory=uuid4)
    prompt: str = Field(..., min_length=1, max_length=500)
    use_sample: bool = Field(default=True, description="Use sample face and audio for preview")


class PreviewResponse(BaseModel):
    """Response containing preview video URL."""
    status: str = "ok"
    url: str
    duration_seconds: Optional[float] = None
    size_px: int = 256
    fps: int = 12


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class DeviceInfo(BaseModel):
    """Device information for processing."""
    device: str
    cuda_available: bool
    cuda_device_count: int = 0
    memory_gb: Optional[float] = None


class ProcessingStatus(BaseModel):
    """Status of a processing task."""
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: float = 0.0  # 0.0 to 1.0
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
