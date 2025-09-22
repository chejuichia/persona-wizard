"""Main FastAPI application for Persona Wizard backend."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.config import settings
from .core.logging import setup_logging, get_logger
from .routes import health, preview, wizard_text, wizard_image, wizard_voice, wizard_build, simple_asr, preview_generation, artifacts

# Set up logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Persona Wizard backend...")
    logger.info(f"Device: {settings.device}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Ensure directories exist
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    settings.models_dir.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Persona Wizard backend...")


# Create FastAPI app
app = FastAPI(
    title="Persona Wizard API",
    description="Backend API for multimodal persona creation",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving generated content
app.mount("/data", StaticFiles(directory=str(settings.data_dir)), name="data")
app.mount("/artifacts-files", StaticFiles(directory=str(settings.artifacts_dir)), name="artifacts-files")
app.mount("/outputs", StaticFiles(directory=str(settings.data_dir / "outputs")), name="outputs")

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(preview.router, tags=["preview"])
app.include_router(wizard_text.router, tags=["wizard-text"])
app.include_router(wizard_image.router, tags=["wizard-image"])
app.include_router(wizard_voice.router, tags=["wizard-voice"])
app.include_router(wizard_build.router, tags=["wizard-build"])
app.include_router(simple_asr.router, tags=["asr"])
app.include_router(preview_generation.router, tags=["preview-generation"])
app.include_router(artifacts.router, tags=["artifacts"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Persona Wizard API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/healthz"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
