"""
ASR WebSocket Routes

Handles real-time speech recognition via WebSocket connections.
Implements local ONNX Whisper for live transcription.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.routing import APIRouter

from ..services.asr.onnx_whisper import ONNXWhisperASR
from ..services.asr.stream_buffer import AudioStreamBuffer
from ..services.audio.vad import VoiceActivityDetector
from ..core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# ASR service instances (one per session)
asr_services: Dict[str, ONNXWhisperASR] = {}

# Audio buffers (one per session)
audio_buffers: Dict[str, AudioStreamBuffer] = {}

# VAD instances (one per session)
vad_instances: Dict[str, VoiceActivityDetector] = {}


class ASRConnectionManager:
    """Manages ASR WebSocket connections and audio processing."""
    
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.asr_services: Dict[str, ONNXWhisperASR] = {}
        self.audio_buffers: Dict[str, AudioStreamBuffer] = {}
        self.vad_instances: Dict[str, VoiceActivityDetector] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.connections[session_id] = websocket
        
        # Initialize services for this session
        self.asr_services[session_id] = ONNXWhisperASR()
        self.audio_buffers[session_id] = AudioStreamBuffer()
        self.vad_instances[session_id] = VoiceActivityDetector()
        
        logger.info(f"ASR WebSocket connected for session {session_id}")
    
    def disconnect(self, session_id: str):
        """Clean up connection and services."""
        if session_id in self.connections:
            del self.connections[session_id]
        
        if session_id in self.asr_services:
            del self.asr_services[session_id]
        
        if session_id in self.audio_buffers:
            del self.audio_buffers[session_id]
        
        if session_id in self.vad_instances:
            del self.vad_instances[session_id]
        
        logger.info(f"ASR WebSocket disconnected for session {session_id}")
    
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
        if session_id not in self.audio_buffers:
            return
        
        # Add audio to buffer
        self.audio_buffers[session_id].add_audio(audio_data, sample_rate)
        
        # Check for voice activity
        if session_id in self.vad_instances:
            is_speech = self.vad_instances[session_id].detect_voice_activity(audio_data)
            
            if is_speech:
                # Get accumulated audio for transcription
                accumulated_audio = self.audio_buffers[session_id].get_audio()
                
                if accumulated_audio and len(accumulated_audio) > 0:
                    try:
                        # Perform transcription
                        if session_id in self.asr_services:
                            result = await self.asr_services[session_id].transcribe_audio(
                                accumulated_audio, 
                                sample_rate
                            )
                            
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
    
    async def finalize_transcription(self, session_id: str):
        """Finalize transcription and send final result."""
        if session_id not in self.audio_buffers:
            return
        
        # Get final audio
        final_audio = self.audio_buffers[session_id].get_audio()
        
        if final_audio and len(final_audio) > 0:
            try:
                # Perform final transcription
                if session_id in self.asr_services:
                    result = await self.asr_services[session_id].transcribe_audio(
                        final_audio, 
                        self.audio_buffers[session_id].sample_rate
                    )
                    
                    if result:
                        # Calculate additional metrics
                        text = result.get("text", "")
                        word_count = len(text.split()) if text else 0
                        duration = len(final_audio) / self.audio_buffers[session_id].sample_rate
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
                        
                        # Clear buffer
                        self.audio_buffers[session_id].clear()
            except Exception as e:
                logger.error(f"Final transcription error for session {session_id}: {e}")
                await self.send_message(session_id, {
                    "type": "error",
                    "message": f"Final transcription failed: {str(e)}"
                })


# Global connection manager
manager = ASRConnectionManager()


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
            "message": "ASR WebSocket connected successfully"
        })
        
        while True:
            try:
                # Receive audio data
                data = await websocket.receive_bytes()
                
                # Process audio chunk
                await manager.process_audio_chunk(session_id, data)
                
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
        manager.disconnect(session_id)


@router.post("/asr/transcribe")
async def transcribe_audio_file(
    request: Request,
    sample_rate: int = 16000,
    language_hint: str = "en"
):
    """
    Transcribe a complete audio file (non-streaming).
    
    This endpoint is useful for testing and one-off transcriptions.
    """
    try:
        # Get audio data from request body
        audio_data = await request.body()
        
        # Create a temporary ASR service
        asr_service = ONNXWhisperASR()
        
        # Perform transcription
        result = await asr_service.transcribe_audio(audio_data, sample_rate)
        
        if result:
            return {
                "status": "ok",
                "text": result.get("text", ""),
                "confidence": result.get("confidence", 0.0),
                "language": result.get("language", language_hint),
                "duration": len(audio_data) / sample_rate
            }
        else:
            return {
                "status": "error",
                "message": "Transcription failed"
            }
    
    except Exception as e:
        logger.error(f"File transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.get("/asr/status")
async def get_asr_status():
    """Get ASR service status and active connections."""
    return {
        "status": "ok",
        "active_connections": len(manager.connections),
        "supported_languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
        "max_duration": 20,  # seconds
        "min_duration": 5,   # seconds
        "sample_rate": 16000
    }
