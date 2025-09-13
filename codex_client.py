"""Codex Client - Interface for routing API calls to Codex CLI"""
from typing import Dict, List, Optional
from datetime import datetime
from anthropic.types import Message, TextBlock, Usage
from claude_code_client import ClaudeCodeClient
from utils import run_subprocess, run_subprocess_async


class CodexClient(ClaudeCodeClient):
    """Client that interfaces with Codex CLI for local inference."""

    def __init__(self):
        super().__init__()
        self.claude_command = "codex"

    def _call_claude_cli(self, prompt: str, model: Optional[str] = None) -> str:
        """Call Codex CLI with the formatted prompt."""
        cmd = [self.claude_command, "--print"]

        if model:
            model_map = {
                "code-davinci-002": "davinci",
                "code-cushman-001": "cushman",
            }
            for full_name, short_name in model_map.items():
                if full_name in model:
                    cmd.extend(["--model", short_name])
                    break
            else:
                for name in ["davinci", "cushman"]:
                    if name in model.lower():
                        cmd.extend(["--model", name])
                        break

        return run_subprocess(cmd, prompt, "Codex")

    def create_message(
        self,
        messages: List[Dict],
        model: str,
        max_tokens: int,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
    ) -> Message:
        message = super().create_message(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            system=system,
            temperature=temperature,
            stream=stream,
        )
        message.id = "msg_codex_" + datetime.now().strftime("%Y%m%d%H%M%S")
        return message

    async def acreate_message(
        self,
        messages: List[Dict],
        model: str,
        max_tokens: int,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
    ) -> Message:
        if stream:
            raise NotImplementedError("Streaming is not yet supported with Codex routing")

        prompt = self._format_messages_for_claude(messages, system)

        cmd = [self.claude_command, "--print"]
        if model:
            model_map = {
                "code-davinci-002": "davinci",
                "code-cushman-001": "cushman",
            }
            for full_name, short_name in model_map.items():
                if full_name in model:
                    cmd.extend(["--model", short_name])
                    break
            else:
                for name in ["davinci", "cushman"]:
                    if name in model.lower():
                        cmd.extend(["--model", name])
                        break

        response_text = await run_subprocess_async(cmd, prompt, "Codex")

        message = Message(
            id="msg_codex_" + datetime.now().strftime("%Y%m%d%H%M%S"),
            content=[TextBlock(text=response_text, type="text")],
            model=model,
            role="assistant",
            stop_reason="end_turn",
            stop_sequence=None,
            type="message",
            usage=Usage(
                input_tokens=len(prompt.split()),
                output_tokens=len(response_text.split()),
                cache_creation_input_tokens=None,
                cache_read_input_tokens=None,
            ),
        )
        return message
