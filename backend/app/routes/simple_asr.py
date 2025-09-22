"""
Simple ASR WebSocket Routes

A simplified ASR service that provides basic transcription
without complex dependencies.
"""

import asyncio
import json
import uuid
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from fastapi.routing import APIRouter

from ..services.asr.local_whisper import LocalWhisperASR
from ..core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# ASR service instances (one per session)
asr_services: Dict[str, LocalWhisperASR] = {}


class SimpleASRConnectionManager:
    """Manages simple ASR WebSocket connections."""
    
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.asr_services: Dict[str, LocalWhisperASR] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.connections[session_id] = websocket
        
        # Initialize ASR service for this session
        self.asr_services[session_id] = LocalWhisperASR(model_size="tiny", device="auto")
        
        logger.info(f"Simple ASR WebSocket connected for session {session_id}")
    
    def disconnect(self, session_id: str):
        """Clean up connection and services."""
        if session_id in self.connections:
            del self.connections[session_id]
        
        if session_id in self.asr_services:
            asyncio.create_task(self.asr_services[session_id].cleanup())
            del self.asr_services[session_id]
        
        logger.info(f"Simple ASR WebSocket disconnected for session {session_id}")
    
    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """Send a message to a specific session."""
        if session_id in self.connections:
            try:
                await self.connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to session {session_id}: {e}")
                self.disconnect(session_id)
    
    async def process_audio_chunk(self, session_id: str, audio_data: bytes, sample_rate: int = 16000):
        """Process an audio chunk for transcription."""
        if session_id not in self.asr_services:
            return
        
        try:
            # Perform transcription
            result = await self.asr_services[session_id].transcribe_audio(audio_data, sample_rate)
            
            if result:
                # Send partial result
                await self.send_message(session_id, {
                    "type": "partial",
                    "text": result.get("text", ""),
                    "confidence": result.get("confidence", 0.0),
                    "language": result.get("language", "en")
                })
        except Exception as e:
            logger.error(f"Transcription error for session {session_id}: {e}")
            await self.send_message(session_id, {
                "type": "error",
                "message": f"Transcription failed: {str(e)}"
            })
    
    async def finalize_transcription(self, session_id: str, audio_data: bytes, sample_rate: int = 16000):
        """Finalize transcription and send final result."""
        if session_id not in self.asr_services:
            return
        
        try:
            # Perform final transcription
            result = await self.asr_services[session_id].transcribe_audio(audio_data, sample_rate)
            
            if result:
                # Calculate additional metrics
                text = result.get("text", "")
                word_count = len(text.split()) if text else 0
                duration = result.get("duration", 0)
                wpm = (word_count / duration * 60) if duration > 0 else 0
                
                # Send final result
                await self.send_message(session_id, {
                    "type": "final",
                    "text": text,
                    "confidence": result.get("confidence", 0.0),
                    "language": result.get("language", "en"),
                    "wpm": round(wpm, 1),
                    "duration": round(duration, 2),
                    "word_count": word_count
                })
        except Exception as e:
            logger.error(f"Final transcription error for session {session_id}: {e}")
            await self.send_message(session_id, {
                "type": "error",
                "message": f"Final transcription failed: {str(e)}"
            })


# Global connection manager
manager = SimpleASRConnectionManager()


@router.websocket("/ws/asr")
async def websocket_asr(websocket: WebSocket, sessionId: str, langHint: str = "en"):
    """
    WebSocket endpoint for real-time speech recognition.
    
    Query parameters:
    - sessionId: Unique session identifier
    - langHint: Language hint for transcription (default: "en")
    """
    session_id = sessionId or str(uuid.uuid4())
    
    try:
        await manager.connect(websocket, session_id)
        
        # Send initial connection confirmation
        await manager.send_message(session_id, {
            "type": "connected",
            "session_id": session_id,
            "language_hint": langHint,
            "message": "Simple ASR WebSocket connected successfully"
        })
        
        # Buffer for accumulating audio
        audio_buffer = b""
        
        while True:
            try:
                # Receive audio data
                data = await websocket.receive_bytes()
                audio_buffer += data
                
                # Process audio chunk every 2 seconds of audio
                if len(audio_buffer) >= 32000:  # ~2 seconds at 16kHz
                    await manager.process_audio_chunk(session_id, audio_buffer)
                    audio_buffer = b""  # Clear buffer after processing
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session {session_id}")
                break
            except Exception as e:
                logger.error(f"Error processing audio for session {session_id}: {e}")
                await manager.send_message(session_id, {
                    "type": "error",
                    "message": f"Audio processing error: {str(e)}"
                })
    
    except Exception as e:
        logger.error(f"WebSocket connection error for session {session_id}: {e}")
    finally:
        # Process any remaining audio
        if audio_buffer:
            await manager.finalize_transcription(session_id, audio_buffer)
        manager.disconnect(session_id)


@router.post("/asr/transcribe")
async def transcribe_audio_file(audio_data: bytes, sample_rate: int = 16000, language_hint: str = "en"):
    """
    Transcribe a complete audio file (non-streaming).
    """
    try:
        # Create a temporary ASR service
        asr_service = LocalWhisperASR(model_size="tiny", device="auto")
        
        # Perform transcription
        result = await asr_service.transcribe_audio(audio_data, sample_rate)
        
        if result:
            return {
                "status": "ok",
                "text": result.get("text", ""),
                "confidence": result.get("confidence", 0.0),
                "language": result.get("language", language_hint),
                "duration": result.get("duration", 0)
            }
        else:
            return {
                "status": "error",
                "message": "Transcription failed"
            }
    
    except Exception as e:
        logger.error(f"File transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        # Cleanup
        await asr_service.cleanup()


@router.post("/asr/download-model")
async def download_whisper_model(model_size: str = "tiny"):
    """Download and cache a Whisper model."""
    try:
        import whisper
        
        logger.info(f"Downloading Whisper model: {model_size}")
        
        # Download the model (this will cache it locally)
        model = whisper.load_model(model_size, download_root=None)
        
        # Get model info
        model_info = {
            "model_size": model_size,
            "is_downloaded": True,
            "device": "auto"
        }
        
        logger.info(f"Whisper model {model_size} downloaded successfully")
        
        return {
            "status": "ok",
            "message": f"Model {model_size} downloaded successfully",
            "model_info": model_info
        }
        
    except Exception as e:
        logger.error(f"Failed to download model {model_size}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download model: {str(e)}")


@router.get("/asr/status")
async def get_asr_status():
    """Get ASR service status and active connections."""
    return {
        "status": "ok",
        "active_connections": len(manager.connections),
        "supported_languages": ["en"],
        "max_duration": 20,  # seconds
        "min_duration": 1,   # seconds
        "sample_rate": 16000,
        "available_models": ["tiny", "base", "small", "medium", "large"]
    }
