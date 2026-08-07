# backend/app/services/audio/voice.py
"""
Audio Processing Service Layer for ClinicalPrep AI v2.0.

Provides Speech-to-Text (STT) transcription using OpenAI Whisper API / local pipeline 
and Text-to-Speech (TTS) voice synthesis.
"""

import os
import tempfile
from io import BytesIO
from typing import Dict, Any
import torch
from transformers import pipeline

device = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_ID = os.getenv("VIBEVOICE_MODEL_PATH", "openai/whisper-tiny")

vibevoice_asr_pipeline = None

try:
    vibevoice_asr_pipeline = pipeline(
        "automatic-speech-recognition",
        model=MODEL_ID,
        device=device,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32
    )
    print(f"✅ Local STT Speech Recognition Pipeline loaded with model: {MODEL_ID}")
except Exception as e:
    print(f"⚠️ Warning: Local STT pipeline init skipped: {e}")


async def transcribe_audio_with_vibevoice(
    audio_bytes: bytes, 
    filename: str = "input.webm"
) -> Dict[str, Any]:
    """
    Transcribes raw WebM/WAV audio binary data into clinical text.
    First attempts local pipeline, falling back directly to OpenAI Whisper API.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    # 1. Primary Cloud Path (Fast & Resilient to WebM formats without FFmpeg issues)
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            audio_file = BytesIO(audio_bytes)
            audio_file.name = filename or "patient_recording.webm"

            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
            
            transcript_text = transcript.text.strip()
            print(f"🎙️ Transcribed Speech: '{transcript_text}'")
            
            return {
                "transcript": transcript_text,
                "segments": [],
                "engine": "OpenAI Hosted Whisper API (whisper-1)"
            }
        except Exception as api_err:
            print(f"⚠️ OpenAI API Transcription error: {api_err}. Trying local model...")

    # 2. Local Model Fallback
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

    raise RuntimeError("No active STT engine available. Check OPENAI_API_KEY or FFmpeg local install.")


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