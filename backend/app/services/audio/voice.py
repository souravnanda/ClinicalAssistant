# backend/app/services/audio/voice.py
"""
Audio Processing Service Layer for ClinicalPrep AI v2.0.

Provides Speech-to-Text (STT) transcription using a local lightweight Hugging Face 
Whisper pipeline with fallback to OpenAI's hosted Whisper API, and Text-to-Speech (TTS) synthesis.
"""

import os
import tempfile
from io import BytesIO
from typing import Dict, Any
import torch
from transformers import pipeline

# Automatically detect CUDA GPU availability for faster local processing
device = "cuda" if torch.cuda.is_available() else "cpu"

# Default to lightweight 150MB model to avoid large cache downloads and timeouts
MODEL_ID = os.getenv("VIBEVOICE_MODEL_PATH", "openai/whisper-tiny")

vibevoice_asr_pipeline = None

try:
    vibevoice_asr_pipeline = pipeline(
        "automatic-speech-recognition",
        model=MODEL_ID,
        device=device,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32
    )
    print(f"✅ STT Speech Recognition Pipeline loaded successfully with model: {MODEL_ID}")
except Exception as e:
    print(f"⚠️ Warning: Could not initialize local STT pipeline for '{MODEL_ID}': {e}")
    print("ℹ️ System will attempt fallback to OpenAI API for transcription requests.")


async def transcribe_audio_with_vibevoice(
    audio_bytes: bytes, 
    filename: str = "input.webm"
) -> Dict[str, Any]:
    """
    Transcribes raw WebM/WAV audio binary data into clinical text.
    Uses local Hugging Face Whisper pipeline first, falling back to OpenAI API if necessary.
    """
    # 1. Primary Path: Local Hugging Face Pipeline
    if vibevoice_asr_pipeline is not None:
        suffix = f".{filename.split('.')[-1]}" if "." in filename else ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name

        try:
            result = vibevoice_asr_pipeline(
                tmp_path,
                return_timestamps=True,
                chunk_length_s=30
            )
            return {
                "transcript": result.get("text", "").strip(),
                "segments": result.get("chunks", []),
                "engine": f"Local ASR ({MODEL_ID})"
            }
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # 2. Fallback Path: OpenAI Hosted Whisper API
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        audio_file = BytesIO(audio_bytes)
        audio_file.name = filename or "audio.webm"

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en"
        )
        return {
            "transcript": transcript.text.strip(),
            "segments": [],
            "engine": "OpenAI Hosted Whisper API (whisper-1)"
        }

    raise RuntimeError("No active STT engine available. Local model failed to load and OPENAI_API_KEY is missing.")


async def synthesize_speech_stream(text_prompt: str) -> bytes:
    """
    Converts assistant response text into synthesized MP3 audio bytes using OpenAI TTS.
    """
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is missing.")

    client = OpenAI(api_key=api_key)
    
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text_prompt,
        response_format="mp3"
    )

    return response.content