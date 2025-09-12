"""
Codex Client - Interface for routing API calls to Codex CLI
"""
import subprocess
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from anthropic.types import Message, TextBlock, Usage
from claude_code_client import ClaudeCodeClient


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

        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error calling Codex"
                raise Exception(f"Codex CLI error: {error_msg}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise Exception("Codex CLI timed out after 120 seconds")
        except FileNotFoundError:
            raise Exception("Codex CLI not found. Please ensure 'codex' is installed and in PATH")
        except Exception as e:
            raise Exception(f"Error calling Codex: {str(e)}")

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

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=prompt.encode()),
                    timeout=120,
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                raise Exception("Codex CLI timed out after 120 seconds")
            if proc.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error calling Codex"
                raise Exception(f"Codex CLI error: {error_msg}")
            response_text = stdout.decode().strip()
        except FileNotFoundError:
            raise Exception("Codex CLI not found. Please ensure 'codex' is installed and in PATH")
        except Exception as e:
            raise Exception(f"Error calling Codex: {str(e)}")

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
