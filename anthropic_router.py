"""
Anthropic API Router that routes to Claude Code when API key is all 9s
"""
import os
from typing import Any, Dict, List, Optional, Union
from anthropic import Anthropic, AsyncAnthropic
from anthropic.types import Message, MessageParam
from anthropic._types import NOT_GIVEN, NotGiven
from claude_code_client import ClaudeCodeClient
from openai_router import OpenAIRouter


class AnthropicRouter:
    """
    A wrapper around the Anthropic client that routes to Claude Code
    when the API key is all 9s, otherwise uses the standard Anthropic API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._is_claude_code_mode = self._check_claude_code_mode()
        
        if self._is_claude_code_mode:
            self.client = ClaudeCodeClient()
        else:
            self.client = Anthropic(api_key=self.api_key)
    
    def _check_claude_code_mode(self) -> bool:
        """Check if the API key is all 9s to enable Claude Code routing."""
        if not self.api_key:
            return False
        # Remove any common prefixes like "sk-ant-" if present
        key_part = self.api_key.split('-')[-1] if '-' in self.api_key else self.api_key
        return all(c == '9' for c in key_part)
    
    @property
    def messages(self):
        """Return a messages interface that mimics Anthropic's API."""
        return MessagesRouter(self)


class MessagesRouter:
    """Routes message creation requests to appropriate backend."""
    
    def __init__(self, router: AnthropicRouter):
        self.router = router
        self.is_claude_code = router._is_claude_code_mode
    
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
        **kwargs
    ) -> Message:
        """
        Create a message completion, routing to Claude Code if appropriate.
        """
        if self.is_claude_code:
            # Route to Claude Code
            return self.router.client.create_message(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                system=system if system is not NOT_GIVEN else None,
                temperature=temperature if temperature is not NOT_GIVEN else None,
                stream=stream if stream is not NOT_GIVEN else False
            )
        else:
            # Use standard Anthropic API
            return self.router.client.messages.create(
                max_tokens=max_tokens,
                messages=messages,
                model=model,
                metadata=metadata,
                stop_sequences=stop_sequences,
                stream=stream,
                system=system,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                **kwargs
            )


class AsyncAnthropicRouter:
    """
    Async version of the AnthropicRouter for async operations.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._is_claude_code_mode = self._check_claude_code_mode()
        
        if self._is_claude_code_mode:
            self.client = ClaudeCodeClient()
        else:
            self.client = AsyncAnthropic(api_key=self.api_key)
    
    def _check_claude_code_mode(self) -> bool:
        """Check if the API key is all 9s to enable Claude Code routing."""
        if not self.api_key:
            return False
        key_part = self.api_key.split('-')[-1] if '-' in self.api_key else self.api_key
        return all(c == '9' for c in key_part)
    
    @property
    def messages(self):
        """Return a messages interface that mimics Anthropic's API."""
        return AsyncMessagesRouter(self)


class AsyncMessagesRouter:
    """Async routes message creation requests to appropriate backend."""
    
    def __init__(self, router: AsyncAnthropicRouter):
        self.router = router
        self.is_claude_code = router._is_claude_code_mode
    
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
        **kwargs
    ) -> Message:
        """
        Create a message completion, routing to Claude Code if appropriate.
        """
        if self.is_claude_code:
            # Route to Claude Code (async wrapper around sync call)
            return await self.router.client.acreate_message(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                system=system if system is not NOT_GIVEN else None,
                temperature=temperature if temperature is not NOT_GIVEN else None,
                stream=stream if stream is not NOT_GIVEN else False
            )
        else:
            # Use standard Anthropic API
            return await self.router.client.messages.create(
                max_tokens=max_tokens,
                messages=messages,
                model=model,
                metadata=metadata,
                stop_sequences=stop_sequences,
                stream=stream,
                system=system,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                **kwargs
            )


# Convenience function to create a client
def create_client(
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    default_provider: str = "claude",
) -> Any:
    """
    Create a client that automatically routes to local inference when the API key is all 9s.

    Args:
        api_key: API key for the selected provider.
        provider: "claude"/"anthropic" or "codex"/"openai". Overrides the default.
        default_provider: Which provider to use if none is specified.

    Returns:
        Router instance for the chosen provider.
    """
    selected = provider or os.environ.get("AI_ROUTER_DEFAULT", default_provider)
    selected = selected.lower()
    if selected in {"codex", "openai"}:
        return OpenAIRouter(api_key=api_key)
    return AnthropicRouter(api_key=api_key)