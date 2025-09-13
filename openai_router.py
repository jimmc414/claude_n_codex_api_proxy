"""
OpenAI API Router that routes to Codex when API key is all 9s
"""
import os
from typing import Any, Dict, List, Optional, Union
from openai import OpenAI, AsyncOpenAI
from anthropic.types import Message, MessageParam, TextBlock, Usage
from anthropic._types import NOT_GIVEN, NotGiven
from codex_client import CodexClient
from utils import is_all_nines_api_key


def _normalize_content(content: Any) -> str:
    """Normalize message content into a plain string for OpenAI."""
    if isinstance(content, dict):
        content_type = content.get("type")
        if content_type == "text":
            return content.get("text", "")
        return f"[{content_type or 'unsupported'} content]"
    if isinstance(content, list):
        parts = [_normalize_content(part).strip() for part in content]
        return " ".join(part for part in parts if part)
    if isinstance(content, str):
        return content
    return str(content)


class OpenAIRouter:
    """A wrapper around the OpenAI client that routes to Codex CLI when the API key is all 9s."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._is_codex_mode = is_all_nines_api_key(self.api_key)
        if self._is_codex_mode:
            self.client = CodexClient()
        else:
            self.client = OpenAI(api_key=self.api_key)

    @property
    def messages(self):
        return MessagesRouter(self)


class MessagesRouter:
    """Routes message creation requests to Codex or OpenAI API."""

    def __init__(self, router: OpenAIRouter):
        self.router = router
        self.is_codex = router._is_codex_mode

    def create(
        self,
        *,
        max_tokens: int,
        messages: List[MessageParam],
        model: str,
        metadata: Union[Dict[str, Any], NotGiven] = NOT_GIVEN,
        stop_sequences: Union[List[str], NotGiven] = NOT_GIVEN,
        stream: Union[bool, NotGiven] = NOT_GIVEN,
        system: Union[str, NotGiven] = NOT_GIVEN,
        temperature: Union[float, NotGiven] = NOT_GIVEN,
        top_k: Union[int, NotGiven] = NOT_GIVEN,
        top_p: Union[float, NotGiven] = NOT_GIVEN,
        **kwargs,
        ) -> Message:
        if self.is_codex:
            if stream is not NOT_GIVEN and stream:
                raise NotImplementedError("Streaming is not yet supported when routing to Codex")
            return self.router.client.create_message(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                system=system if system is not NOT_GIVEN else None,
                temperature=temperature if temperature is not NOT_GIVEN else None,
                stream=False,
            )
        else:
            openai_messages: List[Dict[str, str]] = []
            if system is not NOT_GIVEN and system:
                openai_messages.append({"role": "system", "content": system})
            for msg in messages:
                content = msg.get("content") if isinstance(msg, dict) else msg.content
                content = _normalize_content(content)
                openai_messages.append(
                    {
                        "role": msg.get("role") if isinstance(msg, dict) else msg.role,
                        "content": content,
                    }
                )
            response = self.router.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature if temperature is not NOT_GIVEN else None,
                stop=stop_sequences if stop_sequences is not NOT_GIVEN else None,
                stream=stream if stream is not NOT_GIVEN else False,
                **kwargs,
            )
            if stream is not NOT_GIVEN and stream:
                text_parts: List[str] = []
                first_event = None
                usage = None
                for event in response:
                    if first_event is None:
                        first_event = event
                    delta = getattr(event.choices[0], "delta", None) if event.choices else None
                    if delta is not None:
                        part = getattr(delta, "content", None)
                        if part:
                            text_parts.append(part)
                    if getattr(event, "usage", None):
                        usage = event.usage
                final = first_event
                text = "".join(text_parts)
                usage = usage or getattr(final, "usage", None)
                response_id = getattr(final, "id", "")
            else:
                text = response.choices[0].message.content
                usage = response.usage
                response_id = response.id
            return Message(
                id=response_id,
                content=[TextBlock(text=text, type="text")],
                model=model,
                role="assistant",
                stop_reason="end_turn",
                stop_sequence=None,
                type="message",
                usage=Usage(
                    input_tokens=getattr(usage, "prompt_tokens", 0),
                    output_tokens=getattr(usage, "completion_tokens", 0),
                    cache_creation_input_tokens=None,
                    cache_read_input_tokens=None,
                ),
            )


class AsyncOpenAIRouter:
    """Async version of the OpenAIRouter for async operations."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._is_codex_mode = is_all_nines_api_key(self.api_key)
        if self._is_codex_mode:
            self.client = CodexClient()
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)

    @property
    def messages(self):
        return AsyncMessagesRouter(self)


class AsyncMessagesRouter:
    def __init__(self, router: AsyncOpenAIRouter):
        self.router = router
        self.is_codex = router._is_codex_mode

    async def create(
        self,
        *,
        max_tokens: int,
        messages: List[MessageParam],
        model: str,
        metadata: Union[Dict[str, Any], NotGiven] = NOT_GIVEN,
        stop_sequences: Union[List[str], NotGiven] = NOT_GIVEN,
        stream: Union[bool, NotGiven] = NOT_GIVEN,
        system: Union[str, NotGiven] = NOT_GIVEN,
        temperature: Union[float, NotGiven] = NOT_GIVEN,
        top_k: Union[int, NotGiven] = NOT_GIVEN,
        top_p: Union[float, NotGiven] = NOT_GIVEN,
        **kwargs,
    ) -> Message:
        if self.is_codex:
            if stream is not NOT_GIVEN and stream:
                raise NotImplementedError("Streaming is not yet supported when routing to Codex")
            return await self.router.client.acreate_message(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                system=system if system is not NOT_GIVEN else None,
                temperature=temperature if temperature is not NOT_GIVEN else None,
                stream=False,
            )
        else:
            openai_messages: List[Dict[str, str]] = []
            if system is not NOT_GIVEN and system:
                openai_messages.append({"role": "system", "content": system})
            for msg in messages:
                content = msg.get("content") if isinstance(msg, dict) else msg.content
                content = _normalize_content(content)
                openai_messages.append(
                    {
                        "role": msg.get("role") if isinstance(msg, dict) else msg.role,
                        "content": content,
                    }
                )
            response = await self.router.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature if temperature is not NOT_GIVEN else None,
                stop=stop_sequences if stop_sequences is not NOT_GIVEN else None,
                stream=stream if stream is not NOT_GIVEN else False,
                **kwargs,
            )
            if stream is not NOT_GIVEN and stream:
                text_parts: List[str] = []
                first_event = None
                usage = None
                async for event in response:
                    if first_event is None:
                        first_event = event
                    delta = getattr(event.choices[0], "delta", None) if event.choices else None
                    if delta is not None:
                        part = getattr(delta, "content", None)
                        if part:
                            text_parts.append(part)
                    if getattr(event, "usage", None):
                        usage = event.usage
                final = first_event
                text = "".join(text_parts)
                usage = usage or getattr(final, "usage", None)
                response_id = getattr(final, "id", "")
            else:
                text = response.choices[0].message.content
                usage = response.usage
                response_id = response.id
            return Message(
                id=response_id,
                content=[TextBlock(text=text, type="text")],
                model=model,
                role="assistant",
                stop_reason="end_turn",
                stop_sequence=None,
                type="message",
                usage=Usage(
                    input_tokens=getattr(usage, "prompt_tokens", 0),
                    output_tokens=getattr(usage, "completion_tokens", 0),
                    cache_creation_input_tokens=None,
                    cache_read_input_tokens=None,
                ),
            )


# Convenience function to create an OpenAI client

def create_openai_client(api_key: Optional[str] = None) -> OpenAIRouter:
    return OpenAIRouter(api_key=api_key)
