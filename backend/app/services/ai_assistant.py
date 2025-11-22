"""Utilities for generating AI-assisted chat responses."""
from __future__ import annotations

import logging
from textwrap import dedent
from typing import Sequence

from openai import AsyncOpenAI, OpenAIError

from app.core.config import get_settings
from app.db.models import ChatModel, MessageModel

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


class AISuggestionError(RuntimeError):
    """Raised when an AI suggestion cannot be generated."""


def _get_openai_client() -> AsyncOpenAI:
    """Return a cached AsyncOpenAI client."""
    global _client
    settings = get_settings()
    if not settings.openai_api_key:
        raise AISuggestionError(
            "OpenAI API key is not configured. Please set OPENAI_API_KEY in the backend environment."
        )
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


def _format_history(messages: Sequence[MessageModel], limit: int) -> str:
    """Convert recent chat messages into a readable transcript."""
    if not messages:
        return "No prior messages."

    # Use only the most recent `limit` messages but preserve chronological order.
    trimmed = list(messages)[-limit:]
    lines: list[str] = []
    for message in trimmed:
        speaker = "You" if message.is_sender else "Prospect"
        text = (message.text or "").strip()
        if not text:
            continue
        lines.append(f"{speaker}: {text}")

    return "\n".join(lines) if lines else "Recent messages contained no text."


async def generate_sales_response(
    chat: ChatModel,
    messages: Sequence[MessageModel],
    prompt: str,
    *,
    history_limit: int | None = None,
) -> str:
    """Generate a suggested sales response for a chat."""
    if not prompt or not prompt.strip():
        raise AISuggestionError("Prompt cannot be empty.")

    settings = get_settings()
    effective_limit = history_limit or settings.openai_history_limit or 20
    transcript = _format_history(messages, effective_limit)

    system_message = (
        "You are SetDM, an expert sales development representative who crafts short, "
        "friendly, and confident outbound messages. Tailor every response to the "
        "prospect's context, keep it under 120 words, avoid emojis unless the prospect "
        "used them first, and end with a clear next step."
    )

    user_message = dedent(
        f"""
        Prospect details:
        - Name: {chat.name or "Unknown"}
        - Platform: {chat.account_type}

        Conversation history (oldest first):
        {transcript}

        Prompt from the user:
        {prompt.strip()}

        Write the next message the seller should send. Respond with plain text only.
        """
    ).strip()

    client = _get_openai_client()

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.6,
            max_tokens=400,
        )
    except OpenAIError as exc:
        logger.exception("OpenAI chat completion failed")
        raise AISuggestionError("Failed to generate AI suggestion.") from exc

    if not response.choices:
        raise AISuggestionError("OpenAI returned no suggestions.")

    message_content = response.choices[0].message.content
    if not message_content:
        raise AISuggestionError("OpenAI returned an empty suggestion.")

    return message_content.strip()


