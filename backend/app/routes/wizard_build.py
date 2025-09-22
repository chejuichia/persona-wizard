"""
Wizard Build Routes

Handles persona bundle building and downloading.
"""

from fastapi import APIRouter, HTTPException, Response, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uuid
import time
import shutil
from pathlib import Path

from ..services.bundle.builder import BundleBuilder
from ..core.logging import get_logger
from ..core.config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/wizard/build", tags=["wizard-build"])


class BuildPersonaRequest(BaseModel):
    """Request model for building a persona."""
    text_id: Optional[str] = None
    image_id: Optional[str] = None
    voice_id: Optional[str] = None
    name: str = "My Persona"


class BuildPersonaResponse(BaseModel):
    """Response model for persona build."""
    status: str
    persona_id: str
    bundle_path: str
    artifacts_copied: dict
    size_bytes: int


@router.post("/", response_model=BuildPersonaResponse)
async def build_persona(request: BuildPersonaRequest):
    """
    Build a persona bundle with the provided artifacts.
    
    Creates a complete persona bundle including:
    - persona.yaml manifest
    - All available artifacts (text, image, voice)
    - run_local_inference.py script
    - Configuration files
    - SadTalker checkpoints
    """
    try:
        # Generate unique persona ID
        persona_id = str(uuid.uuid4())
        
        logger.info(f"Building persona {persona_id} with artifacts: "
                   f"text={request.text_id}, image={request.image_id}, voice={request.voice_id}")
        
        # Build the persona bundle
        builder = BundleBuilder()
        bundle_info = builder.build_persona_bundle(
            persona_id=persona_id,
            text_id=request.text_id,
            image_id=request.image_id,
            voice_id=request.voice_id,
            name=request.name
        )
        
        logger.info(f"Successfully built persona {persona_id}")
        
        return BuildPersonaResponse(
            status="ok",
            persona_id=persona_id,
            bundle_path=bundle_info["bundle_path"],
            artifacts_copied=bundle_info["artifacts_copied"],
            size_bytes=bundle_info["size_bytes"]
        )
        
    except Exception as e:
        logger.error(f"Failed to build persona: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to build persona: {str(e)}")


@router.get("/{persona_id}/download")
async def download_bundle(persona_id: str):
    """
    Download a persona bundle as a zip file.
    
    Returns the complete persona bundle including all artifacts and scripts.
    """
    try:
        builder = BundleBuilder()
        bundle_info = builder.get_bundle_info(persona_id)
        
        if not bundle_info:
            raise HTTPException(status_code=404, detail="Persona bundle not found")
        
        bundle_path = Path(bundle_info["bundle_path"])
        
        if not bundle_path.exists():
            raise HTTPException(status_code=404, detail="Bundle file not found")
        
        logger.info(f"Downloading bundle for persona {persona_id}")
        
        return FileResponse(
            path=str(bundle_path),
            filename=f"persona_{persona_id}.zip",
            media_type="application/zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download bundle for persona {persona_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download bundle: {str(e)}")


@router.get("/{persona_id}/info")
async def get_bundle_info(persona_id: str):
    """
    Get information about a persona bundle.
    
    Returns metadata about the bundle without downloading it.
    """
    try:
        builder = BundleBuilder()
        bundle_info = builder.get_bundle_info(persona_id)
        
        if not bundle_info:
            raise HTTPException(status_code=404, detail="Persona bundle not found")
        
        return {
            "status": "ok",
            "persona_id": persona_id,
            "bundle_path": bundle_info["bundle_path"],
            "size_bytes": bundle_info["size_bytes"],
            "created_at": bundle_info["created_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get bundle info for persona {persona_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get bundle info: {str(e)}")


@router.get("/")
async def list_bundles():
    """
    List all available persona bundles.
    
    Returns a list of all created persona bundles with their metadata.
    """
    try:
        builder = BundleBuilder()
        bundles = []
        
        # Scan the outputs directory for bundle files
        outputs_dir = Path(builder.outputs_dir)
        if outputs_dir.exists():
            for bundle_file in outputs_dir.glob("persona_*.zip"):
                # Extract persona_id from filename
                persona_id = bundle_file.stem.replace("persona_", "")
                
                # Get bundle info
                bundle_info = builder.get_bundle_info(persona_id)
                if bundle_info:
                    # Try to load persona.yaml for additional metadata
                    try:
                        persona_dir = builder.personas_dir / persona_id
                        persona_yaml = persona_dir / "persona.yaml"
                        if persona_yaml.exists():
                            import yaml
                            with open(persona_yaml, 'r') as f:
                                persona_data = yaml.safe_load(f)
                            bundle_info["name"] = persona_data.get("name", f"Persona {persona_id}")
                            bundle_info["description"] = persona_data.get("description", "")
                        else:
                            bundle_info["name"] = f"Persona {persona_id}"
                            bundle_info["description"] = ""
                    except Exception as e:
                        logger.warning(f"Failed to load persona.yaml for {persona_id}: {e}")
                        bundle_info["name"] = f"Persona {persona_id}"
                        bundle_info["description"] = ""
                    
                    bundles.append(bundle_info)
        
        # Sort by creation date (newest first)
        bundles.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "status": "ok",
            "bundles": bundles,
            "count": len(bundles)
        }
        
    except Exception as e:
        logger.error(f"Failed to list bundles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list bundles: {str(e)}")


@router.post("/{persona_id}/inference")
async def run_bundle_inference(
    persona_id: str,
    request: Request
):
    """
    Run local inference on a persona bundle.
    
    Extracts the bundle, runs the local inference script, and returns the generated video.
    """
    try:
        # Get request body
        body = await request.json()
        prompt = body.get("prompt", "")
        
        if not prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Check if bundle exists
        builder = BundleBuilder()
        bundle_info = builder.get_bundle_info(persona_id)
        
        if not bundle_info:
            raise HTTPException(status_code=404, detail="Persona bundle not found")
        
        # Extract bundle to temporary directory
        import tempfile
        import zipfile
        import subprocess
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_path = Path(bundle_info["bundle_path"])
            
            # Extract bundle
            with zipfile.ZipFile(bundle_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Change to extracted directory
            os.chdir(temp_dir)
            
            # Run the local inference script using the virtual environment
            python_path = Path(__file__).parent.parent.parent.parent / "venv" / "bin" / "python"
            
            # Set up environment to use the virtual environment
            env = os.environ.copy()
            venv_path = Path(__file__).parent.parent.parent.parent / "venv"
            env["PATH"] = str(venv_path / "bin") + ":" + env.get("PATH", "")
            env["VIRTUAL_ENV"] = str(venv_path)
            
            result = subprocess.run([
                str(python_path), "run_local_inference.py", 
                prompt,
                "--output-dir", "outputs"
            ], capture_output=True, text=True, timeout=300, env=env)  # 5 minute timeout
            
            if result.returncode != 0:
                logger.error(f"Local inference failed: {result.stderr}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Local inference failed: {result.stderr}"
                )
            
            # Look for generated video file
            outputs_dir = Path("outputs")
            video_files = list(outputs_dir.glob("*.mp4"))
            
            if not video_files:
                raise HTTPException(
                    status_code=500, 
                    detail="No video file generated"
                )
            
            # Get the latest video file
            video_file = max(video_files, key=lambda f: f.stat().st_mtime)
            
            # Copy video to a permanent location
            permanent_output_dir = Path(settings.data_dir) / "outputs" / "inference"
            permanent_output_dir.mkdir(parents=True, exist_ok=True)
            
            permanent_video_path = permanent_output_dir / f"inference_{persona_id}_{int(time.time())}.mp4"
            shutil.copy2(video_file, permanent_video_path)
            
            # Get video metadata
            import cv2
            cap = cv2.VideoCapture(str(permanent_video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
            
            return {
                "status": "ok",
                "persona_id": persona_id,
                "prompt": prompt,
                "video_url": f"/outputs/inference/{permanent_video_path.name}",
                "video_path": str(permanent_video_path),
                "duration": duration,
                "fps": fps,
                "size_px": width,
                "frame_count": frame_count,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        
    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Inference timeout")
    except Exception as e:
        logger.error(f"Failed to run bundle inference for persona {persona_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run inference: {str(e)}")
