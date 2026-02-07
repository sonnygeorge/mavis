import base64
import os
from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

from mavis.schema import VLMPrompt

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class VLM(Protocol):
    """Minimal interface for vision-language model inference."""

    def generate(self, prompt: VLMPrompt) -> str:
        """Generate a completion for the given prompt, optionally with images."""
        ...

    def generate_structured(
        self,
        prompt: VLMPrompt,
        response_format: type[T],
    ) -> T:
        """Generate a structured completion constrained to the given Pydantic model."""
        ...


def _encode_image_to_data_url(path: str) -> str:
    """Read an image file and return a base64 data URL."""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    mime = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }.get(ext, "image/png")
    return f"data:{mime};base64,{b64}"


def _build_openai_messages(prompt: VLMPrompt) -> list[dict]:
    """Build an OpenAI-compatible message list from a VLMPrompt."""
    messages: list[dict] = []
    if prompt.system is not None:
        messages.append({"role": "system", "content": prompt.system})

    # Build user content — text-only if no images, multimodal otherwise
    if not prompt.image_paths:
        messages.append({"role": "user", "content": prompt.user})
    else:
        content: list[dict] = [{"type": "text", "text": prompt.user}]
        for img_path in prompt.image_paths:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": _encode_image_to_data_url(img_path)},
                }
            )
        messages.append({"role": "user", "content": content})

    return messages


class OpenAIVLM:
    """OpenAI-compatible VLM implementation using OPENAI_API_KEY and a model name."""

    def __init__(
        self, model: str = "gpt-5.2-2025-12-11", api_key: str | None = None
    ) -> None:
        from openai import OpenAI

        self.model = model
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set or passed explicitly")
        self._client = OpenAI(api_key=api_key)

    def generate(self, prompt: VLMPrompt) -> str:
        messages = _build_openai_messages(prompt)
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content or ""

    def generate_structured(
        self,
        prompt: VLMPrompt,
        response_format: type[T],
    ) -> T:
        messages = _build_openai_messages(prompt)
        response = self._client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            response_format=response_format,
        )
        return response.choices[0].message.parsed
