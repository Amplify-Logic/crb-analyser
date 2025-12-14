"""
Transcription Service

Speech-to-text transcription using Deepgram API.
"""

import logging
from typing import Optional, Tuple

from deepgram import DeepgramClient

from src.config.settings import settings

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for transcribing audio to text using Deepgram."""

    def __init__(self):
        self._client: Optional[DeepgramClient] = None

    @property
    def client(self) -> DeepgramClient:
        """Get or create Deepgram client."""
        if self._client is None:
            if not settings.DEEPGRAM_API_KEY:
                raise ValueError("DEEPGRAM_API_KEY not configured")
            self._client = DeepgramClient(settings.DEEPGRAM_API_KEY)
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
            # Use the listen.rest.v1.transcribe_file method for async transcription
            source = {"buffer": audio_data, "mimetype": mime_type}
            options = {
                "model": "nova-2",
                "smart_format": True,
                "punctuate": True,
                "language": "en",
            }

            response = await self.client.listen.asyncrest.v("1").transcribe_file(
                source, options
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
                    return transcript, confidence

            return "", 0.0

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise


# Singleton instance
transcription_service = TranscriptionService()
