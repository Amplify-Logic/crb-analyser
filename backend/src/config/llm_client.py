"""
Unified LLM Client

Provides a consistent interface for calling different LLM providers:
- Anthropic (Claude): Haiku, Sonnet, Opus
- Google (Gemini): Flash, Pro
- OpenAI (GPT): GPT-5.2, GPT-5.2 Pro
- DeepSeek: V3.2

Verified December 2025 - Supports all major frontier models.

Usage:
    from src.config.llm_client import get_llm_client

    client = get_llm_client()
    response = client.generate(
        model="claude-opus-4-5-20251202",  # or "gemini-3-flash", "gpt-5.2"
        system="You are a helpful assistant",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=1000
    )
"""

import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from src.config.settings import settings

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    def get_provider(self) -> str:
        """Return the provider name."""
        pass


class AnthropicClient(LLMClient):
    """Anthropic Claude client."""

    def __init__(self):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Generate response using Anthropic API."""
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        response = self.client.messages.create(**kwargs)

        return {
            "content": response.content[0].text if response.content else "",
            "model": model,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "provider": "anthropic",
        }

    def get_provider(self) -> str:
        return "anthropic"


class GeminiClient(LLMClient):
    """Google Gemini client."""

    def __init__(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.genai = genai
            self.available = True
        except ImportError:
            logger.warning("google-generativeai not installed. Run: pip install google-generativeai")
            self.available = False
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini client: {e}")
            self.available = False

    def generate(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Generate response using Gemini API."""
        if not self.available:
            raise RuntimeError("Gemini client not available. Install google-generativeai.")

        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            gemini_messages.append({
                "role": role,
                "parts": [msg["content"]]
            })

        # Create model with system instruction
        generation_config = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }

        gemini_model = self.genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
            system_instruction=system if system else None,
        )

        # Generate response
        chat = gemini_model.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])
        response = chat.send_message(gemini_messages[-1]["parts"][0] if gemini_messages else "")

        # Estimate tokens (Gemini doesn't always return exact counts)
        input_tokens = sum(len(m.get("content", "")) // 4 for m in messages)
        output_tokens = len(response.text) // 4

        return {
            "content": response.text,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "provider": "google",
        }

    def get_provider(self) -> str:
        return "google"


class OpenAIClient(LLMClient):
    """OpenAI GPT client (GPT-5.2 and variants)."""

    def __init__(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.available = bool(settings.OPENAI_API_KEY)
        except ImportError:
            logger.warning("openai not installed. Run: pip install openai")
            self.available = False
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")
            self.available = False

    def generate(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Generate response using OpenAI API."""
        if not self.available:
            raise RuntimeError("OpenAI client not available. Set OPENAI_API_KEY.")

        # Build messages with system prompt
        openai_messages = []
        if system:
            openai_messages.append({"role": "system", "content": system})
        openai_messages.extend(messages)

        # GPT-5.x uses max_completion_tokens instead of max_tokens
        if model.startswith("gpt-5"):
            response = self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                max_completion_tokens=max_tokens,
                temperature=temperature,
            )
        else:
            response = self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

        return {
            "content": response.choices[0].message.content or "",
            "model": model,
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
            "provider": "openai",
        }

    def get_provider(self) -> str:
        return "openai"


class DeepSeekClient(LLMClient):
    """DeepSeek V3.2 client (budget option, 94% cheaper)."""

    def __init__(self):
        try:
            from openai import OpenAI
            # DeepSeek uses OpenAI-compatible API
            self.client = OpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com/v1"
            )
            self.available = bool(getattr(settings, 'DEEPSEEK_API_KEY', None))
        except ImportError:
            logger.warning("openai not installed. Run: pip install openai")
            self.available = False
        except Exception as e:
            logger.warning(f"Failed to initialize DeepSeek client: {e}")
            self.available = False

    def generate(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Generate response using DeepSeek API (OpenAI-compatible)."""
        if not self.available:
            raise RuntimeError("DeepSeek client not available. Set DEEPSEEK_API_KEY.")

        # Build messages with system prompt
        deepseek_messages = []
        if system:
            deepseek_messages.append({"role": "system", "content": system})
        deepseek_messages.extend(messages)

        response = self.client.chat.completions.create(
            model=model,
            messages=deepseek_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return {
            "content": response.choices[0].message.content or "",
            "model": model,
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
            "provider": "deepseek",
        }

    def get_provider(self) -> str:
        return "deepseek"


# Singleton clients
_anthropic_client: Optional[AnthropicClient] = None
_gemini_client: Optional[GeminiClient] = None
_openai_client: Optional[OpenAIClient] = None
_deepseek_client: Optional[DeepSeekClient] = None


def get_llm_client(provider: Optional[str] = None) -> LLMClient:
    """
    Get the appropriate LLM client based on provider setting.

    Args:
        provider: Override provider ("anthropic", "google", "openai", "deepseek").
                  If None, uses settings.MODEL_PROVIDER

    Returns:
        LLMClient instance
    """
    global _anthropic_client, _gemini_client, _openai_client, _deepseek_client

    provider = provider or settings.MODEL_PROVIDER

    if provider == "google":
        if _gemini_client is None:
            _gemini_client = GeminiClient()
        if not _gemini_client.available:
            logger.warning("Gemini not available, falling back to Anthropic")
            provider = "anthropic"
        else:
            return _gemini_client

    if provider == "openai":
        if _openai_client is None:
            _openai_client = OpenAIClient()
        if not _openai_client.available:
            logger.warning("OpenAI not available, falling back to Anthropic")
            provider = "anthropic"
        else:
            return _openai_client

    if provider == "deepseek":
        if _deepseek_client is None:
            _deepseek_client = DeepSeekClient()
        if not _deepseek_client.available:
            logger.warning("DeepSeek not available, falling back to Anthropic")
            provider = "anthropic"
        else:
            return _deepseek_client

    # Default to Anthropic
    if _anthropic_client is None:
        _anthropic_client = AnthropicClient()
    return _anthropic_client


def is_gemini_model(model: str) -> bool:
    """Check if a model ID is a Gemini model."""
    return model.startswith("gemini-")


def is_anthropic_model(model: str) -> bool:
    """Check if a model ID is an Anthropic model."""
    return model.startswith("claude-")


def is_openai_model(model: str) -> bool:
    """Check if a model ID is an OpenAI model."""
    return model.startswith("gpt-")


def is_deepseek_model(model: str) -> bool:
    """Check if a model ID is a DeepSeek model."""
    return model.startswith("deepseek-")


def get_client_for_model(model: str) -> LLMClient:
    """
    Get the appropriate client for a specific model.

    This allows mixing models from different providers in the same session.
    """
    if is_gemini_model(model):
        return get_llm_client("google")
    if is_openai_model(model):
        return get_llm_client("openai")
    if is_deepseek_model(model):
        return get_llm_client("deepseek")
    return get_llm_client("anthropic")
