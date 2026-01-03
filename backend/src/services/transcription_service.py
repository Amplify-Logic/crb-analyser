"""
Transcription Service

Speech-to-text using Deepgram API (SDK v5).
Text-to-speech using ElevenLabs API.
"""

import logging
from typing import Optional, Tuple
import asyncio
import httpx

from deepgram import DeepgramClient

from src.config.settings import settings

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for transcribing audio to text (Deepgram) and synthesizing speech (ElevenLabs)."""

    def __init__(self):
        self._deepgram_client: Optional[DeepgramClient] = None

    @property
    def deepgram_client(self) -> DeepgramClient:
        """Get or create Deepgram client for speech-to-text."""
        if self._deepgram_client is None:
            if not settings.DEEPGRAM_API_KEY:
                raise ValueError("DEEPGRAM_API_KEY not configured")
            self._deepgram_client = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)
        return self._deepgram_client

    async def transcribe_audio(
        self,
        audio_data: bytes,
        mime_type: str = "audio/webm",
    ) -> Tuple[str, float]:
        """
        Transcribe audio data to text using Deepgram.

        Args:
            audio_data: Raw audio bytes
            mime_type: MIME type of the audio (default: audio/webm)

        Returns:
            Tuple of (transcribed_text, confidence_score)
        """
        try:
            # Run sync transcription in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.deepgram_client.listen.v1.media.transcribe_file(
                    request=audio_data,
                    model="nova-2",
                    smart_format=True,
                    punctuate=True,
                    language="en",
                )
            )

            # Extract transcript from response
            if (
                response
                and response.results
                and response.results.channels
                and len(response.results.channels) > 0
            ):
                channel = response.results.channels[0]
                if channel.alternatives and len(channel.alternatives) > 0:
                    transcript = channel.alternatives[0].transcript
                    confidence = channel.alternatives[0].confidence
                    logger.info(f"Transcription successful: {len(transcript)} chars, confidence: {confidence}")
                    return transcript, confidence

            logger.warning("No transcript returned from Deepgram")
            return "", 0.0

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise

    async def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
    ) -> bytes:
        """
        Convert text to speech audio using ElevenLabs.

        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID (default from settings)
                     Popular voices:
                     - EXAVITQu4vr4xnSDxMaL: Sarah (conversational)
                     - 21m00Tcm4TlvDq8ikWAM: Rachel (calm, professional)
                     - AZnzlk1XvdvUeBnXmlld: Domi (engaging, friendly)
                     - MF3mGyEYCl7XYWbV9V6O: Elli (friendly, warm)
                     - TxGEqnHWrfWFTfGW9XjX: Josh (deep, authoritative)

        Returns:
            Audio data as bytes (mp3 format)
        """
        if not settings.ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY not configured")

        voice = voice_id or settings.ELEVENLABS_VOICE_ID
        model = settings.ELEVENLABS_MODEL_ID

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": settings.ELEVENLABS_API_KEY,
        }

        payload = {
            "text": text,
            "model_id": model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                audio_data = response.content
                logger.info(f"ElevenLabs TTS generated: {len(audio_data)} bytes for {len(text)} chars")
                return audio_data

        except httpx.HTTPStatusError as e:
            logger.error(f"ElevenLabs API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"TTS error: {e}")
            raise


# Singleton instance
transcription_service = TranscriptionService()
