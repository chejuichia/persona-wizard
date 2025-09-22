"""
Preview Orchestration Service

Orchestrates the complete preview generation pipeline:
LLM → TTS → SadTalker → MP4 output
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from ..llm.text_generator import TextGenerator
from ..tts.voice_cloner import VoiceCloner
from ..lipsync.sadtalker import SadTalkerService
from ...core.config import settings
from ...core.logging import get_logger

logger = get_logger(__name__)


class PreviewOrchestrator:
    """Orchestrates the complete preview generation pipeline."""
    
    def __init__(self):
        """Initialize the preview orchestrator."""
        self.text_generator = TextGenerator()
        self.voice_cloner = VoiceCloner()
        self.sadtalker = SadTalkerService()
        
        # Task tracking
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        
        logger.info("PreviewOrchestrator initialized")
    
    async def generate_preview_with_id(
        self,
        task_id: str,
        prompt: str,
        persona_config: Dict[str, Any],
        voice_profile: Optional[Dict[str, Any]] = None,
        face_image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete preview video with a pre-assigned task ID.
        """
        try:
            # Initialize task tracking
            self.active_tasks[task_id] = {
                "status": "started",
                "progress": 0,
                "steps": [],
                "started_at": datetime.utcnow().isoformat(),
                "prompt": prompt
            }
            
            logger.info(f"Starting preview generation task {task_id}")
            
            # Step 1: Generate text using LLM
            await self._update_task_status(task_id, "generating_text", 10, "Generating text with LLM...")
            
            text_result = await self.text_generator.generate_with_persona(
                prompt=prompt,
                persona_config=persona_config
            )
            
            if "error" in text_result:
                raise Exception(f"Text generation failed: {text_result['error']}")
            
            generated_text = text_result["text"]
            logger.info(f"Generated text: {generated_text[:100]}...")
            
            # Step 2: Generate speech using TTS
            await self._update_task_status(task_id, "generating_speech", 30, "Generating speech with TTS...")
            
            if voice_profile is None:
                # Use default voice profile
                voice_profile = await self._get_default_voice_profile(persona_config)
            
            speech_result = await self.voice_cloner.synthesize_speech(
                text=generated_text,
                voice_profile=voice_profile
            )
            
            if "error" in speech_result:
                raise Exception(f"Speech synthesis failed: {speech_result['error']}")
            
            audio_path = speech_result["output_path"]
            logger.info(f"Generated speech: {audio_path}")
            
            # Step 3: Generate video using SadTalker
            await self._update_task_status(task_id, "generating_video", 60, "Generating video with SadTalker...")
            
            if face_image_path is None:
                # Use default face image from persona config
                face_image_path = self._get_default_face_image(persona_config)
            
            # Create progress callback for SadTalker
            def sadtalker_progress_callback(progress: int, stage: str):
                # Map SadTalker progress (0-100) to overall progress (60-90)
                overall_progress = 60 + int((progress * 0.3))
                # Update task status synchronously
                if task_id in self.active_tasks:
                    self.active_tasks[task_id]["current_step"] = "generating_video"
                    self.active_tasks[task_id]["progress"] = overall_progress
                    self.active_tasks[task_id]["steps"].append({
                        "step": "generating_video",
                        "progress": overall_progress,
                        "message": f"SadTalker: {stage}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    logger.info(f"Task {task_id} progress: {overall_progress}% - SadTalker: {stage}")
            
            video_result = await self.sadtalker.generate_video(
                face_image_path=face_image_path,
                audio_path=audio_path,
                progress_callback=sadtalker_progress_callback
            )
            
            if "error" in video_result:
                raise Exception(f"Video generation failed: {video_result['error']}")
            
            # Step 4: Finalize preview
            await self._update_task_status(task_id, "finalizing", 90, "Finalizing preview...")
            
            preview_result = await self._finalize_preview(
                task_id, text_result, speech_result, video_result
            )
            
            # Mark task as completed
            self.active_tasks[task_id]["status"] = "completed"
            self.active_tasks[task_id]["progress"] = 100
            self.active_tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Preview generation completed: {task_id}")
            return preview_result
            
        except Exception as e:
            logger.error(f"Preview generation failed for task {task_id}: {e}")
            self.active_tasks[task_id]["status"] = "failed"
            self.active_tasks[task_id]["error"] = str(e)
            self.active_tasks[task_id]["failed_at"] = datetime.utcnow().isoformat()
            
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "progress": self.active_tasks[task_id].get("progress", 0)
            }

    async def generate_preview(
        self,
        prompt: str,
        persona_config: Dict[str, Any],
        voice_profile: Optional[Dict[str, Any]] = None,
        face_image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete preview video.
        
        Args:
            prompt: Text prompt for generation
            persona_config: Complete persona configuration
            voice_profile: Voice profile for TTS (optional)
            face_image_path: Path to face image (optional)
            
        Returns:
            Dict with preview generation results
        """
        task_id = str(uuid.uuid4())
        
        try:
            # Initialize task tracking
            self.active_tasks[task_id] = {
                "status": "started",
                "progress": 0,
                "steps": [],
                "started_at": datetime.utcnow().isoformat(),
                "prompt": prompt
            }
            
            logger.info(f"Starting preview generation task {task_id}")
            
            # Step 1: Generate text using LLM
            await self._update_task_status(task_id, "generating_text", 10, "Generating text with LLM...")
            
            text_result = await self.text_generator.generate_with_persona(
                prompt=prompt,
                persona_config=persona_config
            )
            
            if "error" in text_result:
                raise Exception(f"Text generation failed: {text_result['error']}")
            
            generated_text = text_result["text"]
            logger.info(f"Generated text: {generated_text[:100]}...")
            
            # Step 2: Generate speech using TTS
            await self._update_task_status(task_id, "generating_speech", 30, "Generating speech with TTS...")
            
            if voice_profile is None:
                # Use default voice profile
                voice_profile = await self._get_default_voice_profile(persona_config)
            
            speech_result = await self.voice_cloner.synthesize_speech(
                text=generated_text,
                voice_profile=voice_profile
            )
            
            if "error" in speech_result:
                raise Exception(f"Speech synthesis failed: {speech_result['error']}")
            
            audio_path = speech_result["output_path"]
            logger.info(f"Generated speech: {audio_path}")
            
            # Step 3: Generate video using SadTalker
            await self._update_task_status(task_id, "generating_video", 60, "Generating video with SadTalker...")
            
            if face_image_path is None:
                # Use default face image from persona config
                face_image_path = self._get_default_face_image(persona_config)
            
            # Create progress callback for SadTalker
            def sadtalker_progress_callback(progress: int, stage: str):
                # Map SadTalker progress (0-100) to overall progress (60-90)
                overall_progress = 60 + int((progress * 0.3))
                # Update task status synchronously
                if task_id in self.active_tasks:
                    self.active_tasks[task_id]["current_step"] = "generating_video"
                    self.active_tasks[task_id]["progress"] = overall_progress
                    self.active_tasks[task_id]["steps"].append({
                        "step": "generating_video",
                        "progress": overall_progress,
                        "message": f"SadTalker: {stage}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    logger.info(f"Task {task_id} progress: {overall_progress}% - SadTalker: {stage}")
            
            video_result = await self.sadtalker.generate_video(
                face_image_path=face_image_path,
                audio_path=audio_path,
                progress_callback=sadtalker_progress_callback
            )
            
            if "error" in video_result:
                raise Exception(f"Video generation failed: {video_result['error']}")
            
            # Step 4: Finalize preview
            await self._update_task_status(task_id, "finalizing", 90, "Finalizing preview...")
            
            preview_result = await self._finalize_preview(
                task_id, text_result, speech_result, video_result
            )
            
            # Mark task as completed
            self.active_tasks[task_id]["status"] = "completed"
            self.active_tasks[task_id]["progress"] = 100
            self.active_tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Preview generation completed: {task_id}")
            return preview_result
            
        except Exception as e:
            logger.error(f"Preview generation failed for task {task_id}: {e}")
            self.active_tasks[task_id]["status"] = "failed"
            self.active_tasks[task_id]["error"] = str(e)
            self.active_tasks[task_id]["failed_at"] = datetime.utcnow().isoformat()
            
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "progress": self.active_tasks[task_id].get("progress", 0)
            }
    
    async def _update_task_status(
        self, 
        task_id: str, 
        step: str, 
        progress: int, 
        message: str
    ):
        """Update task status."""
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["current_step"] = step
            self.active_tasks[task_id]["progress"] = progress
            self.active_tasks[task_id]["steps"].append({
                "step": step,
                "progress": progress,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _get_default_voice_profile(self, persona_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get default voice profile from persona config."""
        voice_config = persona_config.get("voice", {})
        
        # Try to load an existing voice profile first
        voice_profiles_dir = settings.artifacts_dir / "voice"
        if voice_profiles_dir.exists():
            # Look for any existing voice profile
            for profile_file in voice_profiles_dir.glob("*.json"):
                if "metadata" not in profile_file.name:  # Skip metadata files
                    try:
                        with open(profile_file, 'r') as f:
                            profile = json.load(f)
                            if profile.get("xtts_ready") and profile.get("xtts_voice_id"):
                                logger.info(f"Using existing voice profile: {profile_file.name}")
                                return profile
                    except Exception as e:
                        logger.warning(f"Failed to load voice profile {profile_file}: {e}")
                        continue
        
        # Create a default voice profile with XTTS support
        return {
            "voice_name": "default",
            "speaker_embedding": [0.0] * 256,  # Mock embedding
            "prosody_patterns": {
                "pitch_range": [80, 200],
                "speaking_rate": 150,
                "pitch_mean": 140,
                "energy_mean": 0.5
            },
            "acoustic_features": {
                "mfcc_mean": [0.0] * 13,
                "spectral_centroid": 2000.0,
                "zero_crossing_rate": 0.1
            },
            "xtts_ready": True,  # Enable XTTS synthesis
            "xtts_voice_id": "default",  # Use default voice ID
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "extraction_method": "default"
            }
        }
    
    def _get_default_face_image(self, persona_config: Dict[str, Any]) -> str:
        """Get default face image path from persona config."""
        image_config = persona_config.get("image", {})
        face_ref = image_config.get("face_ref", "artifacts/image/face_ref.png")
        
        # Handle both relative and absolute paths
        if face_ref.startswith("artifacts/"):
            face_path = settings.artifacts_dir / face_ref[10:]  # Remove "artifacts/" prefix
        else:
            face_path = settings.artifacts_dir / face_ref
        
        # Ensure the file exists, if not create a fallback
        if not face_path.exists():
            # Try the direct path
            direct_path = settings.artifacts_dir / "image" / "face_ref.png"
            if direct_path.exists():
                return str(direct_path)
            else:
                # Return the expected path anyway for mock testing
                return str(face_path)
        
        return str(face_path)
    
    async def _finalize_preview(
        self,
        task_id: str,
        text_result: Dict[str, Any],
        speech_result: Dict[str, Any],
        video_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Finalize the preview generation."""
        
        # Create preview metadata
        preview_metadata = {
            "task_id": task_id,
            "status": "completed",
            "generated_at": datetime.utcnow().isoformat(),
            "text": {
                "generated_text": text_result["text"],
                "word_count": text_result["word_count"],
                "char_count": text_result["char_count"],
                "model_name": text_result["model_name"]
            },
            "speech": {
                "audio_path": speech_result["output_path"],
                "duration": speech_result["duration"],
                "sample_rate": speech_result["sample_rate"],
                "voice_name": speech_result["voice_name"]
            },
            "video": {
                "video_path": video_result["output_path"],
                "duration": video_result["duration"],
                "fps": video_result["fps"],
                "size_px": video_result["size_px"],
                "frames": video_result["frames"]
            }
        }
        
        # Save metadata
        metadata_path = settings.data_dir / "outputs" / f"preview_{task_id}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(preview_metadata, f, indent=2)
        
        return {
            "task_id": task_id,
            "status": "completed",
            "progress": 100,
            "video_path": video_result["output_path"],
            "audio_path": speech_result["output_path"],
            "metadata_path": str(metadata_path),
            "preview_metadata": preview_metadata
        }
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a preview generation task."""
        return self.active_tasks.get(task_id)
    
    async def list_active_tasks(self) -> List[Dict[str, Any]]:
        """List all active preview generation tasks."""
        return list(self.active_tasks.values())
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a preview generation task."""
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["status"] = "cancelled"
            self.active_tasks[task_id]["cancelled_at"] = datetime.utcnow().isoformat()
            return True
        return False
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks."""
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        tasks_to_remove = []
        for task_id, task_data in self.active_tasks.items():
            if task_data.get("status") in ["completed", "failed", "cancelled"]:
                completed_at = task_data.get("completed_at") or task_data.get("failed_at") or task_data.get("cancelled_at")
                if completed_at:
                    try:
                        task_time = datetime.fromisoformat(completed_at.replace('Z', '+00:00')).timestamp()
                        if task_time < cutoff_time:
                            tasks_to_remove.append(task_id)
                    except Exception:
                        # If we can't parse the timestamp, remove the task
                        tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.active_tasks[task_id]
        
        logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
    
    def get_orchestrator_info(self) -> Dict[str, Any]:
        """Get orchestrator information."""
        return {
            "active_tasks": len(self.active_tasks),
            "text_generator": self.text_generator.get_model_info(),
            "voice_cloner": self.voice_cloner.get_model_info(),
            "sadtalker": self.sadtalker.get_model_info()
        }
    
    async def cleanup(self):
        """Clean up resources."""
        await self.text_generator.cleanup()
        await self.voice_cloner.cleanup()
        await self.sadtalker.cleanup()
        self.active_tasks.clear()
        logger.info("PreviewOrchestrator cleaned up")


# Global orchestrator instance
orchestrator = PreviewOrchestrator()
