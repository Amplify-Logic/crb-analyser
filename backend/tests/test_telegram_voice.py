"""Tests for voice note transcription."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock, mock_open
from pathlib import Path


@pytest.mark.asyncio
async def test_transcribe_calls_openai_whisper():
    """Should call OpenAI Whisper API with the audio file."""
    mock_transcription = MagicMock()
    mock_transcription.text = "Call the dentist tomorrow"

    mock_client = AsyncMock()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcription)

    with patch("src.telegram.voice.openai.AsyncOpenAI", return_value=mock_client):
        with patch("builtins.open", mock_open(read_data=b"fake audio data")):
            from src.telegram.voice import transcribe_audio

            result = await transcribe_audio(Path("/tmp/test.ogg"))
            assert result == "Call the dentist tomorrow"
            mock_client.audio.transcriptions.create.assert_called_once()
