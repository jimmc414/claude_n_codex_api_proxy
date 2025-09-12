"""
OpenAI API Router that routes to Codex when API key is all 9s
"""
import os
from typing import Any, Dict, List, Optional, Union
from openai import OpenAI, AsyncOpenAI
from anthropic.types import Message, MessageParam, TextBlock, Usage
from anthropic._types import NOT_GIVEN, NotGiven
from codex_client import CodexClient


class OpenAIRouter:
    """A wrapper around the OpenAI client that routes to Codex CLI when the API key is all 9s."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._is_codex_mode = self._check_codex_mode()
        if self._is_codex_mode:
            self.client = CodexClient()
        else:
            self.client = OpenAI(api_key=self.api_key)

    def _check_codex_mode(self) -> bool:
        if not self.api_key:
            return False
        key_part = self.api_key.split('-')[-1] if '-' in self.api_key else self.api_key
        return all(c == '9' for c in key_part)

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
            return self.router.client.create_message(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                system=system if system is not NOT_GIVEN else None,
                temperature=temperature if temperature is not NOT_GIVEN else None,
                stream=stream if stream is not NOT_GIVEN else False,
            )
        else:
            openai_messages = []
            if system is not NOT_GIVEN and system:
                openai_messages.append({"role": "system", "content": system})
            openai_messages.extend(messages)
            response = self.router.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature if temperature is not NOT_GIVEN else None,
                stop=stop_sequences if stop_sequences is not NOT_GIVEN else None,
            )
            text = response.choices[0].message["content"]
            usage = response.usage
            return Message(
                id=response.id,
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
        self._is_codex_mode = self._check_codex_mode()
        if self._is_codex_mode:
            self.client = CodexClient()
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)

    def _check_codex_mode(self) -> bool:
        if not self.api_key:
            return False
        key_part = self.api_key.split('-')[-1] if '-' in self.api_key else self.api_key
        return all(c == '9' for c in key_part)

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
            return await self.router.client.acreate_message(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                system=system if system is not NOT_GIVEN else None,
                temperature=temperature if temperature is not NOT_GIVEN else None,
                stream=stream if stream is not NOT_GIVEN else False,
            )
        else:
            openai_messages = []
            if system is not NOT_GIVEN and system:
                openai_messages.append({"role": "system", "content": system})
            openai_messages.extend(messages)
            response = await self.router.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature if temperature is not NOT_GIVEN else None,
                stop=stop_sequences if stop_sequences is not NOT_GIVEN else None,
            )
            text = response.choices[0].message["content"]
            usage = response.usage
            return Message(
                id=response.id,
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
