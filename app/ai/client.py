"""Claude API client with retry logic, rate limiting, and structured output.

Wraps the Anthropic SDK to provide:
- Exponential backoff on rate limit / transient errors
- Model selection (Sonnet for speed, Opus for complex tasks)
- JSON output parsing with validation
- Token usage tracking
"""

import json
import logging
import time
from typing import Any

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

# Model IDs
MODEL_SONNET = "claude-sonnet-4-20250514"
MODEL_OPUS = "claude-opus-4-20250514"

# Retry config
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
MAX_DELAY = 30.0


class AIClient:
    """Wrapper around the Anthropic SDK for Growth Engine AI tasks."""

    def __init__(self, api_key: str | None = None):
        self._client = anthropic.Anthropic(api_key=api_key or settings.anthropic_api_key)
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    async def generate(
        self,
        prompt: str,
        system: str = "",
        model: str = MODEL_SONNET,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate text completion with retry logic.

        Args:
            prompt: The user message / prompt.
            system: System prompt for context.
            model: Model ID (defaults to Sonnet for cost/speed).
            max_tokens: Maximum output tokens.
            temperature: Sampling temperature.

        Returns:
            The generated text response.
        """
        messages = [{"role": "user", "content": prompt}]

        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system if system else anthropic.NOT_GIVEN,
                    messages=messages,
                )

                self.total_input_tokens += response.usage.input_tokens
                self.total_output_tokens += response.usage.output_tokens

                return response.content[0].text

            except anthropic.RateLimitError:
                delay = min(BASE_DELAY * (2**attempt), MAX_DELAY)
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{MAX_RETRIES}), "
                    f"retrying in {delay:.1f}s"
                )
                time.sleep(delay)

            except anthropic.APIStatusError as e:
                if e.status_code >= 500:
                    delay = min(BASE_DELAY * (2**attempt), MAX_DELAY)
                    logger.warning(
                        f"API error {e.status_code} (attempt {attempt + 1}/{MAX_RETRIES}), "
                        f"retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
                else:
                    raise

        raise RuntimeError(f"Failed after {MAX_RETRIES} retries")

    async def generate_json(
        self,
        prompt: str,
        system: str = "",
        model: str = MODEL_SONNET,
        max_tokens: int = 4096,
        temperature: float = 0.4,
    ) -> dict[str, Any]:
        """Generate a structured JSON response.

        Appends JSON instruction to the prompt, parses the response,
        and retries once on parse failure with a correction prompt.

        Args:
            prompt: The user message (should describe desired JSON structure).
            system: System prompt.
            model: Model ID.
            max_tokens: Maximum output tokens.
            temperature: Lower default for structured output.

        Returns:
            Parsed JSON dict.
        """
        json_instruction = (
            "\n\nRespond with valid JSON only. No markdown fences, no explanation — "
            "just the JSON object."
        )

        raw = await self.generate(
            prompt=prompt + json_instruction,
            system=system,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        try:
            return self._parse_json(raw)
        except json.JSONDecodeError:
            # Retry once with correction
            logger.warning("JSON parse failed, retrying with correction prompt")
            correction = (
                f"Your previous response was not valid JSON. "
                f"Here is what you returned:\n\n{raw[:500]}\n\n"
                f"Please return ONLY valid JSON with no markdown fences or extra text."
            )
            raw = await self.generate(
                prompt=correction,
                system=system,
                model=model,
                max_tokens=max_tokens,
                temperature=0.2,
            )
            return self._parse_json(raw)

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        """Parse JSON from text, stripping markdown fences if present."""
        cleaned = text.strip()

        # Strip markdown code fences
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first line (```json or ```) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()

        return json.loads(cleaned)

    @property
    def usage_summary(self) -> dict:
        """Return cumulative token usage."""
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
        }
