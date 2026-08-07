# backend/app/api/v2/audio.py
"""
Audio Pipeline API Router (v2).

This module defines endpoints for uploading browser voice recordings to be transcribed 
via Microsoft VibeVoice ASR, as well as converting assistant text into speech audio bytes.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Response
from pydantic import BaseModel, Field
from app.services.audio.voice import transcribe_audio_with_vibevoice, synthesize_speech_stream

# Instantiate APIRouter with dedicated prefix and OpenAPI tag documentation
router = APIRouter(prefix="/api/v2/audio", tags=["Audio Pipeline"])


class SpeakPayload(BaseModel):
    """
    Request model enforcing payload structure for Text-to-Speech synthesis.
    """
    text: str = Field(..., description="Assistant text response to be converted into audio bytes.")


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribes uploaded browser multipart audio blobs into clinical text.
    
    Accepts: WebM/WAV audio blob files from React `MediaRecorder`.
    Returns: JSON containing raw transcript text, timestamped segments, and diarization.
    """
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")
            
        # Invoke Microsoft VibeVoice service layer
        result = await transcribe_audio_with_vibevoice(
            audio_bytes=audio_bytes, 
            filename=file.filename or "audio.webm"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VibeVoice STT Processing Error: {str(e)}")


@router.post("/speak")
async def generate_speech(payload: SpeakPayload):
    """
    Synthesizes assistant text responses into streamed MP3 audio bytes.
    
    Accepts: JSON payload containing target text string.
    Returns: Raw audio/mpeg binary response playable in standard HTML5 audio elements.
    """
    if not payload.text:
        raise HTTPException(status_code=400, detail="Text parameter cannot be empty.")

    try:
        audio_bytes = await synthesize_speech_stream(payload.text)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text-to-Speech Synthesis Error: {str(e)}")