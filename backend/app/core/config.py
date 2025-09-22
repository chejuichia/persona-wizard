"""Configuration management for Persona Wizard backend."""

import os
from pathlib import Path
from typing import Literal, Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Server configuration
    host: str = Field(default="0.0.0.0", env="BACKEND_HOST")
    port: int = Field(default=8000, env="BACKEND_PORT")
    debug: bool = Field(default=True, env="BACKEND_DEBUG")
    
    # Device configuration
    device: str = Field(default="auto", env="DEVICE")
    cuda_visible_devices: Optional[str] = Field(default=None, env="CUDA_VISIBLE_DEVICES")
    
    # Feature flags
    asr_backend: Literal["onnx", "foundry"] = Field(default="onnx", env="ASR_BACKEND")
    use_foundry_local: bool = Field(default=True, env="USE_FOUNDRY_LOCAL")
    voice_real: bool = Field(default=True, env="VOICE_REAL")
    style_lora: bool = Field(default=False, env="STYLE_LORA")
    lipsync_engine: str = Field(default="sadtalker", env="LIPSYNC_ENGINE")
    video_mode: Literal["short", "standard", "high"] = Field(default="short", env="VIDEO_MODE")
    
    # LLM configuration
    default_llm_model: str = Field(default="phi-3.5-mini", env="DEFAULT_LLM_MODEL")
    
    # Paths - Use absolute paths to avoid working directory issues
    _project_root: Path = Path(__file__).parent.parent.parent
    models_dir: Path = Field(default=_project_root / "models", env="MODELS_DIR")
    artifacts_dir: Path = Field(default=_project_root / "artifacts", env="ARTIFACTS_DIR")
    data_dir: Path = Field(default=_project_root / "data", env="DATA_DIR")
    
    # SadTalker configuration
    sadtalker_size: int = Field(default=256, env="SADTALKER_SIZE")
    sadtalker_fps: int = Field(default=12, env="SADTALKER_FPS")
    sadtalker_enhancer: str = Field(default="off", env="SADTALKER_ENHANCER")
    
    # Voice configuration
    voice_sample_rate: int = Field(default=16000, env="VOICE_SAMPLE_RATE")
    voice_max_duration: int = Field(default=20, env="VOICE_MAX_DURATION")
    voice_min_duration: int = Field(default=5, env="VOICE_MIN_DURATION")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "tmp").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "outputs").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "uploads").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "personas").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "audio").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "portraits").mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
