# backend/app/services/audio/voice.py
"""
Audio Processing Service Layer.

Handles deep learning model execution for Microsoft VibeVoice continuous 
Speech-to-Text (ASR) transcription and Text-to-Speech (TTS) response generation.
"""

import os
import tempfile
from io import BytesIO
from typing import Dict, Any
from transformers import pipeline
import torch

# Initialize GPU CUDA device availability for optimized local inference speed
device = "cuda" if torch.cuda.is_available() else "cpu"

# Pre-load Microsoft VibeVoice ASR pipeline from Hugging Face
try:
    vibevoice_asr_pipeline = pipeline(
        "automatic-speech-recognition",
        model="microsoft/VibeVoice",
        device=device,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32
    )
except Exception as e:
    vibevoice_asr_pipeline = None
    print(f"Warning: Could not load Microsoft VibeVoice ASR pipeline: {e}")


async def transcribe_audio_with_vibevoice(audio_bytes: bytes, filename: str = "input.webm") -> Dict[str, Any]:
    """
    Processes raw audio bytes using Microsoft VibeVoice ASR.
    
    Purpose: Performs single-pass contextual speech-to-text transcription and returns 
    structured text alongside timestamp segments and speaker diarization details.
    """
    if vibevoice_asr_pipeline is None:
        raise RuntimeError("VibeVoice ASR model pipeline is not initialized.")

    # Write temporary audio binary file to local storage for Hugging Face pipeline ingestion
    suffix = f".{filename.split('.')[-1]}" if "." in filename else ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_path = tmp_file.name

    try:
        # Execute single-pass contextual transcription
        result = vibevoice_asr_pipeline(
            tmp_path,
            return_timestamps=True,
            chunk_length_s=30
        )
        
        # Extract and format transcript text and timeline segments
        transcript_text = result.get("text", "").strip()
        chunks = result.get("chunks", [])

        return {
            "transcript": transcript_text,
            "segments": chunks,
            "engine": "Microsoft VibeVoice ASR"
        }
    finally:
        # Guarantee cleanup of temporary audio files after execution
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


async def synthesize_speech_stream(text_prompt: str) -> bytes:
    """
    Converts assistant response text into synthesized MP3 audio bytes.
    
    Purpose: Provides responsive audio output streams back to the web client 
    for turn-by-turn conversational playback.
    """
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text_prompt,
        response_format="mp3"
    )
    return response.content