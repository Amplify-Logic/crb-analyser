"""
Voice Note Handler

Transcribes Telegram voice notes using OpenAI Whisper API,
then routes the text through the intent classifier.
"""

import logging
import tempfile
from pathlib import Path

import openai
from telegram import Update
from telegram.ext import ContextTypes

from src.config.settings import settings
from src.telegram.bot import admin_guard

logger = logging.getLogger(__name__)


async def transcribe_audio(audio_path: Path) -> str:
    """Transcribe an audio file using OpenAI Whisper API."""
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    with open(audio_path, "rb") as audio_file:
        transcription = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )

    return transcription.text


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming voice notes — transcribe and route."""
    if not await admin_guard(update, context):
        return

    if not settings.OPENAI_API_KEY:
        await update.message.reply_text("Voice notes require OPENAI_API_KEY to be set.")
        return

    voice = update.message.voice or update.message.audio
    if not voice:
        return

    await update.message.reply_text("Transcribing...")

    try:
        # Download voice file
        file = await context.bot.get_file(voice.file_id)

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            tmp_path = Path(tmp.name)

        # Transcribe
        text = await transcribe_audio(tmp_path)

        # Clean up
        tmp_path.unlink(missing_ok=True)

        if not text.strip():
            await update.message.reply_text("Could not transcribe voice note.")
            return

        # Show transcription
        await update.message.reply_text(f"Heard: _{text}_", parse_mode="Markdown")

        # Route transcribed text through intent classifier
        from src.telegram.handlers.message_handler import route_text

        await route_text(update, text)

    except Exception as e:
        logger.error(f"Voice transcription failed: {e}")
        await update.message.reply_text(f"Voice transcription failed: {e}")
