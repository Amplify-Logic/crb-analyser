"""
Transcription Service

Speech-to-text and text-to-speech using Deepgram API (SDK v5).
"""

import logging
from typing import Optional, Tuple
import asyncio

from deepgram import DeepgramClient

from src.config.settings import settings

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for transcribing audio to text and synthesizing speech using Deepgram."""

    def __init__(self):
        self._client: Optional[DeepgramClient] = None

    @property
    def client(self) -> DeepgramClient:
        """Get or create Deepgram client."""
        if self._client is None:
            if not settings.DEEPGRAM_API_KEY:
                raise ValueError("DEEPGRAM_API_KEY not configured")
            self._client = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)
        return self._client

    async def transcribe_audio(
        self,
        audio_data: bytes,
        mime_type: str = "audio/webm",
    ) -> Tuple[str, float]:
        """
        Transcribe audio data to text.

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
                lambda: self.client.listen.v1.media.transcribe_file(
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
        voice: str = "aura-asteria-en",  # Natural female voice
    ) -> bytes:
        """
        Convert text to speech audio.

        Args:
            text: Text to convert to speech
            voice: Voice model to use (default: aura-asteria-en)
                   Options: aura-asteria-en, aura-luna-en, aura-stella-en,
                           aura-athena-en, aura-hera-en, aura-orion-en,
                           aura-arcas-en, aura-perseus-en, aura-angus-en,
                           aura-orpheus-en, aura-helios-en, aura-zeus-en
                           Aura 2 voices also available (aura-2-*)

        Returns:
            Audio data as bytes (mp3 format)
        """
        try:
            # Run sync TTS in thread pool
            loop = asyncio.get_event_loop()

            def generate_audio():
                # generate() returns an Iterator[bytes]
                audio_iterator = self.client.speak.v1.audio.generate(
                    text=text,
                    model=voice,
                    encoding="mp3",
                )
                # Collect all bytes from the iterator
                audio_chunks = list(audio_iterator)
                return b"".join(audio_chunks)

            audio_data = await loop.run_in_executor(None, generate_audio)
            logger.info(f"TTS generated: {len(audio_data)} bytes for {len(text)} chars")
            return audio_data

        except Exception as e:
            logger.error(f"TTS error: {e}")
            raise


# Singleton instance
transcription_service = TranscriptionService()
