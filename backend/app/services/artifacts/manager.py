"""
Artifact Manager Service

Manages and retrieves previously uploaded artifacts (audio, text, images)
for reuse across wizard steps.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ...core.config import settings
from ...core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ArtifactInfo:
    """Information about a previously uploaded artifact."""
    id: str
    type: str  # 'audio', 'text', 'image'
    name: str
    created_at: str
    file_path: str
    metadata: Dict[str, Any]
    size: Optional[int] = None
    duration: Optional[float] = None  # For audio
    dimensions: Optional[tuple] = None  # For images (width, height)


class ArtifactManager:
    """Manages previously uploaded artifacts for reuse."""
    
    def __init__(self):
        self.artifacts_dir = Path(settings.artifacts_dir)
        self.audio_dir = self.artifacts_dir / "voice"
        self.text_dir = self.artifacts_dir / "text"
        self.image_dir = self.artifacts_dir / "image"
        
        # Ensure directories exist
        for dir_path in [self.audio_dir, self.text_dir, self.image_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_audio_artifacts(self) -> List[ArtifactInfo]:
        """Get all previously uploaded audio artifacts."""
        artifacts = []
        
        try:
            for audio_file in self.audio_dir.glob("*.wav"):
                # Look for corresponding metadata file
                metadata_file = audio_file.with_suffix('.json')
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        # Get file size
                        file_size = audio_file.stat().st_size
                        
                        # Extract duration from metadata or calculate
                        duration = metadata.get('duration', 0)
                        
                        artifact = ArtifactInfo(
                            id=audio_file.stem,
                            type='audio',
                            name=metadata.get('voice_name', audio_file.stem),
                            created_at=metadata.get('created_at', datetime.now().isoformat()),
                            file_path=str(audio_file),
                            metadata=metadata,
                            size=file_size,
                            duration=duration
                        )
                        artifacts.append(artifact)
                        
                    except Exception as e:
                        logger.warning(f"Failed to load metadata for {audio_file}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Failed to scan audio artifacts: {e}")
        
        # Sort by creation date (newest first)
        artifacts.sort(key=lambda x: x.created_at, reverse=True)
        return artifacts
    
    def get_text_artifacts(self) -> List[ArtifactInfo]:
        """Get all previously uploaded text artifacts."""
        artifacts = []
        
        try:
            for text_file in self.text_dir.glob("*_style_profile.json"):
                try:
                    with open(text_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Get file size
                    file_size = text_file.stat().st_size
                    
                    # Extract text length from metadata
                    text_length = metadata.get('metadata', {}).get('text_length', 0)
                    
                    artifact = ArtifactInfo(
                        id=text_file.stem.replace('_style_profile', ''),
                        type='text',
                        name=f"Text Upload ({text_length} chars)",
                        created_at=metadata.get('metadata', {}).get('created_at', datetime.now().isoformat()),
                        file_path=str(text_file),
                        metadata=metadata,
                        size=file_size
                    )
                    artifacts.append(artifact)
                    
                except Exception as e:
                    logger.warning(f"Failed to load text artifact {text_file}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to scan text artifacts: {e}")
        
        # Sort by creation date (newest first)
        artifacts.sort(key=lambda x: x.created_at, reverse=True)
        return artifacts
    
    def get_image_artifacts(self) -> List[ArtifactInfo]:
        """Get all previously uploaded image artifacts."""
        artifacts = []
        
        try:
            for image_file in self.image_dir.glob("*_face_ref.png"):
                try:
                    # Look for corresponding metadata file
                    metadata_file = image_file.with_suffix('.json')
                    
                    metadata = {}
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                    
                    # Get file size
                    file_size = image_file.stat().st_size
                    
                    # Extract dimensions from metadata or use default
                    dimensions = metadata.get('dimensions', (256, 256))
                    
                    artifact = ArtifactInfo(
                        id=image_file.stem.replace('_face_ref', ''),
                        type='image',
                        name=f"Portrait ({dimensions[0]}x{dimensions[1]})",
                        created_at=metadata.get('created_at', datetime.now().isoformat()),
                        file_path=str(image_file),
                        metadata=metadata,
                        size=file_size,
                        dimensions=dimensions
                    )
                    artifacts.append(artifact)
                    
                except Exception as e:
                    logger.warning(f"Failed to load image artifact {image_file}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to scan image artifacts: {e}")
        
        # Sort by creation date (newest first)
        artifacts.sort(key=lambda x: x.created_at, reverse=True)
        return artifacts
    
    def get_all_artifacts(self) -> Dict[str, List[ArtifactInfo]]:
        """Get all artifacts grouped by type."""
        return {
            'audio': self.get_audio_artifacts(),
            'text': self.get_text_artifacts(),
            'image': self.get_image_artifacts()
        }
    
    def get_artifact_by_id(self, artifact_id: str, artifact_type: str) -> Optional[ArtifactInfo]:
        """Get a specific artifact by ID and type."""
        try:
            if artifact_type == 'audio':
                artifacts = self.get_audio_artifacts()
            elif artifact_type == 'text':
                artifacts = self.get_text_artifacts()
            elif artifact_type == 'image':
                artifacts = self.get_image_artifacts()
            else:
                return None
            
            for artifact in artifacts:
                if artifact.id == artifact_id:
                    return artifact
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get artifact {artifact_id} of type {artifact_type}: {e}")
            return None
    
    def delete_artifact(self, artifact_id: str, artifact_type: str) -> bool:
        """Delete an artifact by ID and type."""
        try:
            artifact = self.get_artifact_by_id(artifact_id, artifact_type)
            if not artifact:
                return False
            
            # Delete the file
            file_path = Path(artifact.file_path)
            if file_path.exists():
                file_path.unlink()
            
            # Delete metadata file if it exists
            metadata_file = file_path.with_suffix('.json')
            if metadata_file.exists():
                metadata_file.unlink()
            
            logger.info(f"Deleted artifact {artifact_id} of type {artifact_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete artifact {artifact_id} of type {artifact_type}: {e}")
            return False
    
    def get_artifact_stats(self) -> Dict[str, Any]:
        """Get statistics about stored artifacts."""
        try:
            all_artifacts = self.get_all_artifacts()
            
            stats = {
                'total_artifacts': sum(len(artifacts) for artifacts in all_artifacts.values()),
                'by_type': {
                    artifact_type: len(artifacts) 
                    for artifact_type, artifacts in all_artifacts.items()
                },
                'total_size': 0,
                'oldest_artifact': None,
                'newest_artifact': None
            }
            
            all_dates = []
            for artifacts in all_artifacts.values():
                for artifact in artifacts:
                    stats['total_size'] += artifact.size or 0
                    all_dates.append(artifact.created_at)
            
            if all_dates:
                all_dates.sort()
                stats['oldest_artifact'] = all_dates[0]
                stats['newest_artifact'] = all_dates[-1]
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get artifact stats: {e}")
            return {
                'total_artifacts': 0,
                'by_type': {'audio': 0, 'text': 0, 'image': 0},
                'total_size': 0,
                'oldest_artifact': None,
                'newest_artifact': None
            }
