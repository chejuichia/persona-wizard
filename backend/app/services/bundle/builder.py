"""
Bundle Builder Service

Creates persona bundles with artifacts and run_local_inference.py script.
Implements short-first defaults for CPU-friendly operation.
"""

import os
import yaml
import zipfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from ...core.config import settings
from ...core.logging import get_logger

logger = get_logger(__name__)


class BundleBuilder:
    """Builds persona bundles with all required artifacts."""
    
    def __init__(self):
        self.data_dir = Path(settings.data_dir)
        self.artifacts_dir = Path(settings.artifacts_dir)
        self.personas_dir = self.data_dir / "personas"
        self.outputs_dir = self.data_dir / "outputs"
        
        # Ensure directories exist
        self.personas_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    def build_persona_bundle(
        self,
        persona_id: str,
        text_id: Optional[str] = None,
        image_id: Optional[str] = None,
        voice_id: Optional[str] = None,
        name: str = "My Persona"
    ) -> Dict[str, Any]:
        """
        Build a complete persona bundle.
        
        Args:
            persona_id: Unique identifier for the persona
            text_id: Optional text upload ID
            image_id: Optional image upload ID  
            voice_id: Optional voice clone ID
            name: Human-readable persona name
            
        Returns:
            Dict with bundle info and file paths
        """
        logger.info(f"Building persona bundle for {persona_id}")
        
        # Create persona directory
        persona_dir = self.personas_dir / persona_id
        persona_dir.mkdir(parents=True, exist_ok=True)
        
        # Create artifacts subdirectories
        artifacts_subdirs = ["text", "voice", "image", "video"]
        for subdir in artifacts_subdirs:
            (persona_dir / "artifacts" / subdir).mkdir(parents=True, exist_ok=True)
        
        # Copy artifacts if they exist
        artifacts_copied = {}
        
        # Copy text artifacts
        if text_id:
            text_artifacts = self._copy_text_artifacts(text_id, persona_dir)
            artifacts_copied.update(text_artifacts)
        
        # Copy image artifacts
        if image_id:
            image_artifacts = self._copy_image_artifacts(image_id, persona_dir)
            artifacts_copied.update(image_artifacts)
        
        # Copy voice artifacts
        if voice_id:
            voice_artifacts = self._copy_voice_artifacts(voice_id, persona_dir)
            artifacts_copied.update(voice_artifacts)
        
        # Copy SadTalker checkpoints and models (use symlinks for efficiency)
        self._copy_sadtalker_ckpts(persona_dir)
        self._copy_sadtalker_models(persona_dir)
        
        # Create persona.yaml manifest
        persona_manifest = self._create_persona_manifest(
            persona_id, name, artifacts_copied
        )
        
        # Write persona.yaml
        manifest_path = persona_dir / "persona.yaml"
        with open(manifest_path, 'w') as f:
            yaml.dump(persona_manifest, f, default_flow_style=False)
        
        # Create run_local_inference.py script
        self._create_inference_script(persona_dir)
        
        # Create config files
        self._create_config_files(persona_dir)
        
        # Create zip bundle
        bundle_path = self._create_zip_bundle(persona_id, persona_dir)
        
        logger.info(f"Bundle created at {bundle_path}")
        
        return {
            "persona_id": persona_id,
            "bundle_path": str(bundle_path),
            "manifest_path": str(manifest_path),
            "artifacts_copied": artifacts_copied,
            "size_bytes": bundle_path.stat().st_size if bundle_path.exists() else 0
        }
    
    def _copy_text_artifacts(self, text_id: str, persona_dir: Path) -> Dict[str, str]:
        """Copy text-related artifacts."""
        artifacts = {}
        
        # Copy style profile
        style_profile_src = self.artifacts_dir / "text" / f"{text_id}_style_profile.json"
        if style_profile_src.exists():
            style_profile_dst = persona_dir / "artifacts" / "text" / "style_profile.json"
            shutil.copy2(style_profile_src, style_profile_dst)
            artifacts["style_profile"] = "artifacts/text/style_profile.json"
        
        # Copy raw text
        raw_text_src = self.artifacts_dir / "text" / f"{text_id}_raw.txt"
        if raw_text_src.exists():
            raw_text_dst = persona_dir / "artifacts" / "text" / "raw.txt"
            shutil.copy2(raw_text_src, raw_text_dst)
            artifacts["raw_text"] = "artifacts/text/raw.txt"
        
        return artifacts
    
    def _copy_image_artifacts(self, image_id: str, persona_dir: Path) -> Dict[str, str]:
        """Copy image-related artifacts."""
        artifacts = {}
        
        # Copy face reference image
        face_ref_src = self.artifacts_dir / "image" / f"{image_id}_face_ref.png"
        if face_ref_src.exists():
            face_ref_dst = persona_dir / "artifacts" / "image" / "face_ref.png"
            shutil.copy2(face_ref_src, face_ref_dst)
            artifacts["face_ref"] = "artifacts/image/face_ref.png"
        
        return artifacts
    
    def _copy_voice_artifacts(self, voice_id: str, persona_dir: Path) -> Dict[str, str]:
        """Copy voice-related artifacts."""
        artifacts = {}
        
        # Copy XTTS speaker profile (JSON format)
        speaker_src = self.artifacts_dir / "voice" / f"{voice_id}_xtts_speaker.json"
        if speaker_src.exists():
            speaker_dst = persona_dir / "artifacts" / "voice" / "xtts_speaker.json"
            shutil.copy2(speaker_src, speaker_dst)
            artifacts["speaker_profile"] = "artifacts/voice/xtts_speaker.json"
        
        # Copy voice metadata
        voice_meta_src = self.artifacts_dir / "voice" / f"{voice_id}_metadata.json"
        if voice_meta_src.exists():
            voice_meta_dst = persona_dir / "artifacts" / "voice" / "metadata.json"
            shutil.copy2(voice_meta_src, voice_meta_dst)
            artifacts["voice_metadata"] = "artifacts/voice/metadata.json"
        
        # Copy processed WAV file as reference audio (preferred)
        wav_src = self.artifacts_dir / "voice" / f"{voice_id}.wav"
        if wav_src.exists():
            # Use the processed WAV file directly
            reference_dst = persona_dir / "artifacts" / "voice" / "reference.wav"
            shutil.copy2(wav_src, reference_dst)
            artifacts["reference_audio"] = "artifacts/voice/reference.wav"
            artifacts["voice_id"] = voice_id
        else:
            # Fallback: Copy original WebM file and convert to WAV
            original_src = self.artifacts_dir / "voice" / f"{voice_id}_original.webm"
            if original_src.exists():
                # Convert WebM to WAV for XTTS compatibility
                reference_dst = persona_dir / "artifacts" / "voice" / "reference.wav"
                self._convert_webm_to_wav(original_src, reference_dst)
                artifacts["reference_audio"] = "artifacts/voice/reference.wav"
                artifacts["voice_id"] = voice_id
        
        return artifacts
    
    def _convert_webm_to_wav(self, webm_path: Path, wav_path: Path):
        """Convert WebM audio to WAV format for XTTS compatibility."""
        try:
            import subprocess
            
            # Use ffmpeg to convert WebM to WAV
            cmd = [
                'ffmpeg', '-y',
                '-i', str(webm_path),
                '-acodec', 'pcm_s16le',
                '-ar', '22050',  # XTTS standard sample rate
                '-ac', '1',      # Mono
                str(wav_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.warning(f"FFmpeg conversion failed: {result.stderr}")
                # Fallback: just copy the file
                shutil.copy2(webm_path, wav_path)
            else:
                logger.info(f"Converted {webm_path} to {wav_path}")
                
        except Exception as e:
            logger.warning(f"Error converting WebM to WAV: {e}")
            # Fallback: just copy the file
            shutil.copy2(webm_path, wav_path)
    
    def _copy_sadtalker_ckpts(self, persona_dir: Path):
        """Copy SadTalker checkpoints."""
        sadtalker_src = Path("artifacts/video/sadtalker_ckpts")
        if sadtalker_src.exists():
            sadtalker_dst = persona_dir / "artifacts" / "video" / "sadtalker_ckpts"
            shutil.copytree(sadtalker_src, sadtalker_dst, dirs_exist_ok=True)
    
    def _copy_sadtalker_models(self, persona_dir: Path):
        """Create symlinks to SadTalker models for efficient bundle creation."""
        try:
            # Create symlinks to SadTalker models from backend/models/sadtalker
            # Use absolute path resolution - go up from builder.py to backend root
            current_file = Path(__file__).resolve()
            # builder.py -> bundle -> services -> app -> backend
            backend_dir = current_file.parent.parent.parent.parent
            sadtalker_models_dir = backend_dir / "models" / "sadtalker"
            
            if sadtalker_models_dir.exists():
                # Create symlinks for checkpoints directory
                checkpoints_dst = persona_dir / "checkpoints"
                if (sadtalker_models_dir / "checkpoints").exists():
                    if checkpoints_dst.exists():
                        checkpoints_dst.unlink()
                    checkpoints_dst.symlink_to(sadtalker_models_dir / "checkpoints")
                    logger.info(f"Created symlink to SadTalker checkpoints")
                
                # Create symlinks for gfpgan weights
                gfpgan_dst = persona_dir / "gfpgan"
                if (sadtalker_models_dir / "gfpgan").exists():
                    if gfpgan_dst.exists():
                        shutil.rmtree(gfpgan_dst)
                    gfpgan_dst.symlink_to(sadtalker_models_dir / "gfpgan")
                    logger.info(f"Created symlink to SadTalker GFPGAN weights")
                
                # Copy config files (small files, safe to copy)
                config_dst = persona_dir / "config"
                config_dst.mkdir(parents=True, exist_ok=True)
                if (sadtalker_models_dir / "config").exists():
                    shutil.copytree(sadtalker_models_dir / "config", config_dst, dirs_exist_ok=True)
                    logger.info(f"Copied SadTalker config files to bundle")
        except Exception as e:
            logger.warning(f"Failed to create SadTalker model symlinks: {e}")
            # Fallback: try copying only essential small files
            try:
                self._copy_essential_sadtalker_files(persona_dir, sadtalker_models_dir)
            except Exception as fallback_e:
                logger.warning(f"Fallback SadTalker file copying also failed: {fallback_e}")
    
    def _copy_essential_sadtalker_files(self, persona_dir: Path, sadtalker_models_dir: Path):
        """Copy only essential small SadTalker files as fallback."""
        try:
            # Copy only the config directory (small files)
            config_dst = persona_dir / "config"
            config_dst.mkdir(parents=True, exist_ok=True)
            if (sadtalker_models_dir / "config").exists():
                shutil.copytree(sadtalker_models_dir / "config", config_dst, dirs_exist_ok=True)
                logger.info(f"Copied essential SadTalker config files")
        except Exception as e:
            logger.warning(f"Failed to copy essential SadTalker files: {e}")
    
    def _create_persona_manifest(
        self, 
        persona_id: str, 
        name: str, 
        artifacts: Dict[str, str]
    ) -> Dict[str, Any]:
        """Create persona.yaml manifest."""
        # Load voice metadata if available
        voice_metadata = {}
        if artifacts.get("voice_metadata"):
            try:
                import json
                # Find the voice metadata file
                voice_meta_files = list(self.artifacts_dir.glob("voice/*_metadata.json"))
                if voice_meta_files:
                    with open(voice_meta_files[0], 'r') as f:
                        voice_metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load voice metadata: {e}")
        
        # Load text metadata if available
        text_metadata = {}
        if artifacts.get("style_profile"):
            try:
                import json
                # Find the style profile file
                style_profile_files = list(self.artifacts_dir.glob("text/*_style_profile.json"))
                if style_profile_files:
                    with open(style_profile_files[0], 'r') as f:
                        style_data = json.load(f)
                        text_metadata = style_data.get("metadata", {})
            except Exception as e:
                logger.warning(f"Failed to load text metadata: {e}")
        
        return {
            "id": persona_id,
            "name": name,
            "created_utc": datetime.utcnow().isoformat() + "Z",
            
            "text": {
                "base_model": "phi-3.5-mini",
                "style": {
                    "mode": "profile" if artifacts.get("style_profile") else "default",
                    "adapter_path": artifacts.get("style_profile", "artifacts/text/style_profile.json")
                },
                "generation": {
                    "max_new_tokens": 256,
                    "temperature": 0.7,
                    "top_p": 0.9
                },
                "metadata": {
                    "word_count": text_metadata.get("word_count", 0),
                    "character_count": text_metadata.get("character_count", 0),
                    "extraction_method": "uploaded" if artifacts.get("style_profile") else "default"
                }
            },
            
            "voice": {
                "tts_engine": "xtts-v2",
                "voice_id": artifacts.get("voice_id", "default_voice"),
                "reference_audio": artifacts.get("reference_audio", "artifacts/voice/reference.wav"),
                "speaker_profile": artifacts.get("speaker_profile", "artifacts/voice/xtts_speaker.json"),
                "sample_rate_hz": voice_metadata.get("sample_rate", 16000),
                "metadata": {
                    "language": voice_metadata.get("language", "en"),
                    "duration": voice_metadata.get("duration", 0),
                    "reference_text": voice_metadata.get("reference_text", ""),
                    "speaking_rate": "medium",
                    "pitch": "neutral",
                    "energy": "calm",
                    "extraction_method": "uploaded" if artifacts.get("speaker_profile") else "default"
                }
            },
            
            "image": {
                "face_ref": artifacts.get("face_ref", "artifacts/image/face_ref.png"),
                "metadata": {
                    "extraction_method": "uploaded" if artifacts.get("face_ref") else "default"
                }
            },
            
            "video": {
                "lipsync_engine": "sadtalker",
                "mode": "short",  # short | standard | high
                "size_px": 256,
                "fps": 12,
                "enhancer": "off"
            },
            
            "guardrails": {
                "enabled": True,
                "blocked_categories": [
                    "sexual-minors",
                    "graphic-violence", 
                    "self-harm",
                    "illegal-instructions"
                ],
                "regex_blocklist": [
                    r"(?i)credit card number\b",
                    r"(?i)social security number\b"
                ],
                "max_output_chars": 1200
            }
        }
    
    def _create_inference_script(self, persona_dir: Path):
        """Create run_local_inference.py script."""
        # Copy service modules to bundle
        self._copy_service_modules(persona_dir)
        
        # Generate the script content with all fixes
        script_content = self._generate_script_content()
        script_path = persona_dir / "run_local_inference.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        script_path.chmod(0o755)
        logger.info(f"Generated inference script at {script_path}")
    
    def _copy_service_modules(self, persona_dir: Path):
        """Copy all necessary service modules and dependencies to the bundle."""
        try:
            # Create complete app directory structure in bundle
            app_dir = persona_dir / "app"
            services_dir = app_dir / "services"
            core_dir = app_dir / "core"
            tts_dir = services_dir / "tts"
            lipsync_dir = services_dir / "lipsync"
            llm_dir = services_dir / "llm"
            foundry_dir = services_dir / "foundry"
            
            # Create all directories
            core_dir.mkdir(parents=True, exist_ok=True)
            tts_dir.mkdir(parents=True, exist_ok=True)
            lipsync_dir.mkdir(parents=True, exist_ok=True)
            llm_dir.mkdir(parents=True, exist_ok=True)
            foundry_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy core modules (config, logging, etc.)
            core_src = Path(__file__).parent.parent.parent / "core"
            if core_src.exists():
                for core_file in core_src.glob("*.py"):
                    if core_file.name != "__pycache__":
                        core_dst = core_dir / core_file.name
                        shutil.copy2(core_file, core_dst)
                logger.info(f"Copied core modules to bundle")
            
            # Copy TTS services
            tts_src = Path(__file__).parent.parent / "tts"
            if tts_src.exists():
                for tts_file in tts_src.glob("*.py"):
                    if tts_file.name != "__pycache__":
                        tts_dst = tts_dir / tts_file.name
                        shutil.copy2(tts_file, tts_dst)
                logger.info(f"Copied TTS services to bundle")
            
            # Copy lip-sync services
            lipsync_src = Path(__file__).parent.parent / "lipsync"
            if lipsync_src.exists():
                for lipsync_file in lipsync_src.glob("*.py"):
                    if lipsync_file.name != "__pycache__":
                        lipsync_dst = lipsync_dir / lipsync_file.name
                        shutil.copy2(lipsync_file, lipsync_dst)
                logger.info(f"Copied lip-sync services to bundle")
            
            # Copy LLM services
            llm_src = Path(__file__).parent.parent / "llm"
            if llm_src.exists():
                for llm_file in llm_src.glob("*.py"):
                    if llm_file.name != "__pycache__":
                        llm_dst = llm_dir / llm_file.name
                        shutil.copy2(llm_file, llm_dst)
                logger.info(f"Copied LLM services to bundle")
            
            # Copy Foundry services
            foundry_src = Path(__file__).parent.parent / "foundry"
            if foundry_src.exists():
                for foundry_file in foundry_src.glob("*.py"):
                    if foundry_file.name != "__pycache__":
                        foundry_dst = foundry_dir / foundry_file.name
                        shutil.copy2(foundry_file, foundry_dst)
                logger.info(f"Copied Foundry services to bundle")
            
            # Create __init__.py files for all directories
            (app_dir / "__init__.py").touch()
            (core_dir / "__init__.py").touch()
            (services_dir / "__init__.py").touch()
            (tts_dir / "__init__.py").touch()
            (lipsync_dir / "__init__.py").touch()
            (llm_dir / "__init__.py").touch()
            (foundry_dir / "__init__.py").touch()
            
            # Copy any additional utility modules
            self._copy_utility_modules(persona_dir)
            
        except Exception as e:
            logger.warning(f"Failed to copy service modules: {e}")
    
    def _copy_utility_modules(self, persona_dir: Path):
        """Copy utility modules and helper functions."""
        try:
            # Copy any utility modules that might be needed
            utils_dir = persona_dir / "utils"
            utils_dir.mkdir(exist_ok=True)
            
            # Create a basic utils module if needed
            utils_init = utils_dir / "__init__.py"
            if not utils_init.exists():
                utils_init.touch()
            
            # Copy any device detection utilities
            device_utils = utils_dir / "device.py"
            if not device_utils.exists():
                device_utils.write_text('''"""
Device detection utilities for the persona bundle.
"""

import torch

def get_device():
    """Get the best available device for inference."""
    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"

def get_device_info():
    """Get detailed device information."""
    device = get_device()
    info = {"device": device}
    
    if device == "cuda":
        info["cuda_version"] = torch.version.cuda
        info["gpu_count"] = torch.cuda.device_count()
        if torch.cuda.device_count() > 0:
            info["gpu_name"] = torch.cuda.get_device_name(0)
    
    return info
''')
            
            logger.info(f"Copied utility modules to bundle")
            
        except Exception as e:
            logger.warning(f"Failed to copy utility modules: {e}")

    def _create_config_files(self, persona_dir: Path):
        """Create configuration files for the bundle."""
        try:
            config_dir = persona_dir / "configs"
            config_dir.mkdir(exist_ok=True)
            
            # TTS config
            tts_config = {
                "engine": "xtts-v2",
                "model_path": "artifacts/voice/xtts_speaker.pth",
                "sample_rate": 16000,
                "device": "auto"
            }
            
            with open(config_dir / "tts.yaml", 'w') as f:
                yaml.dump(tts_config, f, default_flow_style=False)
            
            # SadTalker config
            sadtalker_config = {
                "mode": "short",
                "size_px": 256,
                "fps": 12,
                "enhancer": "off",
                "device": "auto"
            }
            
            with open(config_dir / "sadtalker.yaml", 'w') as f:
                yaml.dump(sadtalker_config, f, default_flow_style=False)
            
            # LLM config
            llm_config = {
                "model": "phi4-mini",
                "max_new_tokens": 256,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            with open(config_dir / "llm.yaml", 'w') as f:
                yaml.dump(llm_config, f, default_flow_style=False)
            
            logger.info(f"Created config files in {config_dir}")
            
        except Exception as e:
            logger.warning(f"Failed to create config files: {e}")

    def _create_zip_bundle(self, persona_id: str, persona_dir: Path) -> Path:
        """Create zip bundle of the persona directory, handling symlinks."""
        try:
            import zipfile
            from datetime import datetime
            
            bundle_path = self.outputs_dir / f"persona_{persona_id}.zip"
            
            with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in persona_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(persona_dir)
                        try:
                            # Try to add the file normally
                            zipf.write(file_path, arcname)
                        except (OSError, FileNotFoundError):
                            # If it's a symlink that can't be followed, skip it
                            logger.warning(f"Skipping symlink: {file_path}")
                            continue
                    elif file_path.is_symlink():
                        # Handle symlinks by following them
                        try:
                            target_path = file_path.readlink()
                            if target_path.is_absolute():
                                # For absolute symlinks, use the target directly
                                target_path = Path(target_path)
                            else:
                                # For relative symlinks, resolve relative to the symlink
                                target_path = file_path.parent / target_path
                            
                            if target_path.exists():
                                if target_path.is_file():
                                    arcname = file_path.relative_to(persona_dir)
                                    zipf.write(target_path, arcname)
                                    logger.info(f"Added symlink target: {file_path} -> {target_path}")
                                elif target_path.is_dir():
                                    # For directory symlinks, add all files in the directory
                                    for sub_file in target_path.rglob('*'):
                                        if sub_file.is_file():
                                            rel_path = sub_file.relative_to(target_path)
                                            arcname = file_path.relative_to(persona_dir) / rel_path
                                            zipf.write(sub_file, arcname)
                                    logger.info(f"Added symlink directory contents: {file_path} -> {target_path}")
                            else:
                                logger.warning(f"Symlink target not found: {file_path} -> {target_path}")
                        except Exception as symlink_e:
                            logger.warning(f"Failed to handle symlink {file_path}: {symlink_e}")
            
            logger.info(f"Created zip bundle: {bundle_path}")
            return bundle_path
            
        except Exception as e:
            logger.error(f"Failed to create zip bundle: {e}")
            raise

    def _generate_script_content(self) -> str:
        """Generate the complete script content with all fixes and dependencies."""
        # Read the updated script from the existing persona directory
        updated_script_path = self.data_dir / "personas" / "6a7c1889-b2c9-4f71-914f-75b6739ba7b5" / "run_local_inference.py"
        if updated_script_path.exists():
            with open(updated_script_path, 'r') as f:
                return f.read()
        
        # Generate a comprehensive script with all dependencies
        return self._generate_comprehensive_script()
    
    def _generate_comprehensive_script(self) -> str:
        """Generate a comprehensive inference script with all dependencies."""
        return '''#!/usr/bin/env python3
"""
Local Persona Inference Script

Runs persona inference locally using the bundled artifacts.
Supports text generation, voice synthesis, and lip-sync video generation.
Includes all necessary dependencies and error handling.
"""

import os
import sys
import yaml
import argparse
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile
import shutil

# Change to script directory to ensure relative paths work
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Add current directory to path for imports
sys.path.insert(0, script_dir)

# Add backend directory to path for app imports
backend_dir = os.path.abspath(os.path.join(script_dir, '../../..'))
sys.path.insert(0, backend_dir)

# Also add the backend/app directory specifically
app_dir = os.path.join(backend_dir, 'app')
sys.path.insert(0, app_dir)

# Debug: print paths
print(f"Current working directory: {os.getcwd()}")
print(f"Script directory: {script_dir}")
print(f"Backend directory: {backend_dir}")
print(f"App directory: {app_dir}")
print(f"Python path: {sys.path[:5]}")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s')
logger = logging.getLogger(__name__)

def load_persona_config() -> Dict[str, Any]:
    """Load persona configuration from persona.yaml."""
    config_path = Path("persona.yaml")
    if not config_path.exists():
        raise FileNotFoundError("persona.yaml not found in current directory")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def _adapt_prompt_to_style(prompt: str, style_profile: Dict[str, Any]) -> str:
    """Adapt prompt based on style profile."""
    if not style_profile:
        return prompt
    
    # Extract style characteristics
    style_metrics = style_profile.get("style_metrics", {})
    tone = style_profile.get("tone", {})
    
    # Build style context
    style_context = []
    
    # Add vocabulary richness info
    if "vocabulary_richness" in style_metrics:
        richness = style_metrics["vocabulary_richness"]
        if richness > 0.7:
            style_context.append("Use sophisticated vocabulary")
        elif richness < 0.3:
            style_context.append("Use simple, accessible language")
    
    # Add sentence length preference
    if "avg_sentence_length" in style_metrics:
        avg_length = style_metrics["avg_sentence_length"]
        if avg_length > 20:
            style_context.append("Use longer, more complex sentences")
        elif avg_length < 10:
            style_context.append("Use shorter, concise sentences")
    
    # Add tone guidance
    if "primary_tone" in tone:
        primary_tone = tone["primary_tone"]
        style_context.append(f"Maintain a {primary_tone} tone")
    
    # Combine with original prompt
    if style_context:
        style_instruction = " ".join(style_context)
        return f"{style_instruction}. {prompt}"
    
    return prompt

def generate_text(prompt: str, config: Dict[str, Any]) -> str:
    """Generate text using the persona's style profile."""
    logger.info(f"Generating text for prompt: {prompt}")
    
    try:
        # Try to use Foundry Local first
        import requests
        import json
        
        # Get text configuration
        text_config = config.get("text", {})
        generation_config = text_config.get("generation", {})
        model_name = text_config.get("base_model", "phi-3.5-mini")
        
        # Load style profile if available
        style_profile = None
        if text_config.get("style", {}).get("mode") == "profile":
            style_path = text_config["style"]["adapter_path"]
            if os.path.exists(style_path):
                logger.info(f"Loading style profile from: {style_path}")
                with open(style_path, 'r') as f:
                    style_profile = json.load(f)
                logger.info(f"Style profile loaded: {style_profile.get('tone', {}).get('primary_tone', 'unknown')} tone")
        
        # Apply style adaptation to prompt
        adapted_prompt = prompt
        if style_profile:
            adapted_prompt = _adapt_prompt_to_style(prompt, style_profile)
            logger.info(f"Style-adapted prompt: {adapted_prompt}")
        
        # Try Foundry Local API
        foundry_url = "http://127.0.0.1:53224"
        
        # Check if Foundry Local is available
        try:
            # Check if models endpoint is available
            models_response = requests.get(f"{foundry_url}/v1/models", timeout=5)
            if models_response.status_code == 200:
                logger.info(f"Using Foundry Local with model: {model_name}")
                
                # Use the correct model ID from Foundry Local
                model_id = "Phi-3.5-mini-instruct-generic-gpu"
                
                # Generate text via Foundry Local
                payload = {
                    "model": model_id,
                    "messages": [{"role": "user", "content": adapted_prompt}],
                    "max_tokens": generation_config.get("max_new_tokens", 256),
                    "temperature": generation_config.get("temperature", 0.7)
                }
                
                response = requests.post(
                    f"{foundry_url}/v1/chat/completions",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    generated_text = result["choices"][0]["message"]["content"]
                    logger.info(f"Generated text: {generated_text}")
                    return generated_text
                else:
                    logger.error(f"Foundry Local API error: {response.status_code}")
                    raise Exception(f"Foundry Local API error: {response.status_code}")
            else:
                raise Exception("Foundry Local not responding")
                
        except Exception as foundry_error:
            logger.warning(f"Foundry Local failed: {foundry_error}")
            raise RuntimeError(f"Text generation failed: {foundry_error}")
        
    except Exception as e:
        logger.error(f"Error in text generation: {e}")
        raise

def synthesize_voice(text: str, config: Dict[str, Any]) -> str:
    """Synthesize voice using the cloned voice profile."""
    logger.info(f"Synthesizing voice for: {text}")
    
    try:
        # Import real XTTS service
        from app.services.tts.xtts_real import RealXTTSService
        
        # Initialize XTTS service
        xtts = RealXTTSService()
        
        # Get voice configuration
        voice_config = config.get("voice", {})
        voice_id = voice_config.get("voice_id", "default_voice")
        reference_audio = voice_config.get("reference_audio", "artifacts/voice/reference.wav")
        
        # Clone voice if not already done
        if voice_id not in xtts.speaker_embeddings:
            logger.info(f"Cloning voice {voice_id} from reference audio: {reference_audio}")
            clone_result = xtts.clone_voice(reference_audio, voice_id)
            if clone_result["status"] != "success":
                raise RuntimeError(f"Voice cloning failed: {clone_result.get('error', 'Unknown error')}")
        
        # Synthesize speech
        output_path = "voice_output.wav"
        logger.info(f"Synthesizing speech with voice {voice_id}")
        synthesis_result = xtts.synthesize_speech(text, voice_id, output_path)
        
        if synthesis_result["status"] == "success":
            logger.info(f"✅ Generated audio: {output_path}")
            return output_path
        else:
            raise RuntimeError(f"Voice synthesis failed: {synthesis_result.get('error', 'Unknown error')}")
        
    except ImportError as e:
        logger.error(f"❌ Import error in voice synthesis: {e}")
        logger.error(f"   This usually means the app module is not in the Python path")
        logger.error(f"   Current working directory: {os.getcwd()}")
        logger.error(f"   Python path: {sys.path[:3]}")
        raise
    except FileNotFoundError as e:
        logger.error(f"❌ File not found in voice synthesis: {e}")
        logger.error(f"   Expected reference audio: {reference_audio}")
        logger.error(f"   Current working directory: {os.getcwd()}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in voice synthesis: {e}")
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Current working directory: {os.getcwd()}")
        raise

def generate_video(text: str, audio_path: str, config: Dict[str, Any], output_dir: str = "outputs") -> str:
    """Generate lip-sync video using SadTalker."""
    logger.info(f"Generating video for: {text}")
    
    try:
        # Import real SadTalker service
        from app.services.lipsync.sadtalker_real import RealSadTalkerService
        
        # Create a local SadTalker service that uses bundle models
        class LocalSadTalkerService:
            def __init__(self):
                self.device = "cpu"  # Use CPU for local inference
                self.models_initialized = False
                self._initialize_models()
            
            def _initialize_models(self):
                """Initialize SadTalker models using local bundle paths."""
                try:
                    import sadtalker
                    from sadtalker.utils.init_path import init_path
                    from sadtalker.utils.preprocess import CropAndExtract
                    from sadtalker.test_audio2coeff import Audio2Coeff
                    from sadtalker.facerender.animate import AnimateFromCoeff
                    from sadtalker.generate_batch import get_data
                    from sadtalker.generate_facerender_batch import get_facerender_data
                    
                    # Use local bundle model paths
                    checkpoint_dir = os.path.join(script_dir, "checkpoints")
                    config_dir = os.path.join(script_dir, "config")
                    
                    # Initialize paths
                    self.sadtalker_paths = init_path(
                        checkpoint_dir, 
                        config_dir, 
                        size=256,
                        old_version=False,
                        preprocess='crop'
                    )
                    
                    # Initialize models
                    self.preprocess_model = CropAndExtract(self.sadtalker_paths, self.device)
                    self.audio2coeff = Audio2Coeff(self.sadtalker_paths, self.device)
                    self.animate_from_coeff = AnimateFromCoeff(self.sadtalker_paths, self.device)
                    self.get_data = get_data
                    self.get_facerender_data = get_facerender_data
                    
                    self.models_initialized = True
                    logger.info("✅ Local SadTalker models initialized successfully")
                    
                except Exception as e:
                    logger.error(f"❌ Error initializing local SadTalker models: {e}")
                    raise RuntimeError(f"Local SadTalker model initialization failed: {e}")
            
            async def generate_video(self, face_image_path, audio_path, output_path):
                """Generate video using local models."""
                if not self.models_initialized:
                    raise RuntimeError("SadTalker models are not initialized.")
                
                try:
                    import tempfile
                    import shutil
                    
                    temp_dir = Path(tempfile.mkdtemp())
                    logger.info(f"Created temporary directory: {temp_dir}")
                    
                    # Step 1: Extract 3DMM from source image
                    first_coeff_path, crop_pic_path, crop_info = self.preprocess_model.generate(
                        face_image_path, temp_dir, 'crop', source_image_flag=True, pic_size=256
                    )
                    logger.info(f"✅ Preprocessing completed. First coeff path: {first_coeff_path}")
                    
                    # Step 2: Audio to coefficients
                    batch = self.get_data(first_coeff_path, audio_path, self.device, None, still=False)
                    logger.info(f"✅ get_data completed. Batch keys: {list(batch.keys()) if batch else 'None'}")
                    
                    coeff_path = self.audio2coeff.generate(batch, temp_dir, 0, None)
                    logger.info(f"✅ audio2coeff.generate completed. Coeff path: {coeff_path}")
                    
                    # Step 3: Generate facerender data
                    facerender_batch = self.get_facerender_data(coeff_path, crop_pic_path, first_coeff_path, audio_path, 2, None, None, None)
                    logger.info(f"✅ Facerender batch created. Keys: {list(facerender_batch.keys())}")
                    
                    # Step 4: Generate final video
                    result_video_path = self.animate_from_coeff.generate(
                        facerender_batch,
                        temp_dir,
                        face_image_path,
                        crop_info,
                        enhancer=None,
                        background_enhancer=None,
                        preprocess='crop',
                        img_size=256
                    )
                    logger.info(f"✅ SadTalker video generation completed. Output: {result_video_path}")
                    
                    # Copy the video to the final output path
                    import shutil
                    final_output_path = Path(output_path)
                    final_output_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(result_video_path, final_output_path)
                    logger.info(f"✅ Copied video to final location: {final_output_path}")
                    
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                    
                    return {
                        "status": "success",
                        "output_path": str(final_output_path),
                        "duration": 0,
                        "message": "Local SadTalker video generation completed successfully"
                    }
                    
                except Exception as e:
                    logger.error(f"❌ Error in local SadTalker video generation: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise RuntimeError(f"Local SadTalker video generation failed: {e}")
        
        # Initialize local SadTalker service
        sadtalker = LocalSadTalkerService()
        
        # Get image configuration
        image_config = config.get("image", {})
        face_ref_path = image_config.get("face_ref", "artifacts/image/face_ref.png")
        
        # Ensure output directory exists
        from pathlib import Path
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate lip-sync video
        final_video_path = output_path / "output_video.mp4"
        logger.info(f"Generating video with face: {face_ref_path}, audio: {audio_path}")
        
        # Run the async generate_video method
        result = asyncio.run(sadtalker.generate_video(
            face_image_path=face_ref_path,
            audio_path=audio_path,
            output_path=str(final_video_path)
        ))
        
        if result["status"] == "success":
            logger.info(f"✅ Generated lip-sync video: {final_video_path}")
            return str(final_video_path)
        else:
            raise RuntimeError(f"SadTalker failed: {result.get('error', 'Unknown error')}")
        
    except ImportError as e:
        logger.error(f"❌ Import error in video generation: {e}")
        logger.error(f"   This usually means the app module is not in the Python path")
        logger.error(f"   Current working directory: {os.getcwd()}")
        logger.error(f"   Python path: {sys.path[:3]}")
        raise
    except FileNotFoundError as e:
        logger.error(f"❌ File not found in video generation: {e}")
        logger.error(f"   Expected face image: {face_ref_path}")
        logger.error(f"   Expected audio: {audio_path}")
        logger.error(f"   Current working directory: {os.getcwd()}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in video generation: {e}")
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Current working directory: {os.getcwd()}")
        raise

    def get_bundle_info(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a persona bundle.
        
        Args:
            persona_id: The persona ID to get info for
            
        Returns:
            Dict with bundle info or None if not found
        """
        try:
            bundle_path = self.outputs_dir / f"persona_{persona_id}.zip"
            
            if not bundle_path.exists():
                return None
            
            # Get file stats
            stat = bundle_path.stat()
            created_at = datetime.fromtimestamp(stat.st_ctime)
            
            return {
                "persona_id": persona_id,
                "bundle_path": str(bundle_path),
                "size_bytes": stat.st_size,
                "created_at": created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get bundle info for {persona_id}: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description="Run local persona inference")
    parser.add_argument("prompt", help="Text prompt for the persona")
    parser.add_argument("--output-dir", default="outputs", help="Output directory")
    parser.add_argument("--text-only", action="store_true", help="Generate text only")
    parser.add_argument("--voice-only", action="store_true", help="Generate voice only")
    
    args = parser.parse_args()
    
    try:
        # Load persona configuration
        logger.info("📋 Loading persona configuration...")
        config = load_persona_config()
        logger.info(f"✅ Loaded persona: {config['name']}")
        
        # Create output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Output directory: {output_dir.absolute()}")
        
        # Generate text
        logger.info("🤖 Generating text...")
        generated_text = generate_text(args.prompt, config)
        logger.info(f"✅ Generated text: {generated_text}")
        
        if not args.text_only:
            # Synthesize voice
            logger.info("🎤 Synthesizing voice...")
            audio_path = synthesize_voice(generated_text, config)
            logger.info(f"✅ Generated audio: {audio_path}")
            
            if not args.voice_only:
                # Generate video
                logger.info("🎬 Generating video...")
                video_path = generate_video(generated_text, audio_path, config, args.output_dir)
                logger.info(f"✅ Generated video: {video_path}")
        
        logger.info("🎉 Inference completed successfully!")
        
    except FileNotFoundError as e:
        logger.error(f"❌ File not found: {e}")
        logger.error(f"   Current working directory: {os.getcwd()}")
        sys.exit(1)
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error(f"   This usually means the app module is not in the Python path")
        logger.error(f"   Current working directory: {os.getcwd()}")
        logger.error(f"   Python path: {sys.path[:3]}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Current working directory: {os.getcwd()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

    def get_bundle_info(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a persona bundle.
        
        Args:
            persona_id: The persona ID to get info for
            
        Returns:
            Dict with bundle info or None if not found
        """
        try:
            bundle_path = self.outputs_dir / f"persona_{persona_id}.zip"
            
            if not bundle_path.exists():
                return None
            
            # Get file stats
            stat = bundle_path.stat()
            created_at = datetime.fromtimestamp(stat.st_ctime)
            
            return {
                "persona_id": persona_id,
                "bundle_path": str(bundle_path),
                "size_bytes": stat.st_size,
                "created_at": created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get bundle info for {persona_id}: {e}")
            return None
