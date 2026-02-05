"""Provider-agnostic LLM inference abstraction."""

import os
from typing import Protocol, runtime_checkable

from mavis.schema import PromptPair


@runtime_checkable
class LLM(Protocol):
    """Minimal interface for LLM inference. Implementations are provider-specific."""

    def generate(self, prompt: PromptPair) -> str:
        """Generate a completion for the given system/user prompt pair."""
        ...


class OpenAILLM:
    """OpenAI-compatible LLM implementation using OPENAI_API_KEY and a model name."""

    def __init__(
        self, model: str = "gpt-5.2-2025-12-11", api_key: str | None = None
    ) -> None:
        from openai import OpenAI

        self.model = model
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set or passed explicitly")
        self._client = OpenAI(api_key=api_key)

    def generate(self, prompt: PromptPair) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt.system},
                {"role": "user", "content": prompt.user},
            ],
        )
        return response.choices[0].message.content or ""
