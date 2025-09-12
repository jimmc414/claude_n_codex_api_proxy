"""
Codex Proxy Handler - Handles API requests routed through the proxy for Codex CLI.
"""
import asyncio
from typing import Any, Dict, Optional
from claude_code_proxy_handler import ClaudeCodeProxyHandler, MAX_PROMPT_LENGTH, logger

CODEX_VALID_MODELS = {
    "code-davinci-002",
    "code-cushman-001",
}


class CodexProxyHandler(ClaudeCodeProxyHandler):
    """Proxy handler that routes requests to the Codex CLI."""

    def __init__(self):
        super().__init__()
        self.claude_command = "codex"

    def _validate_model(self, model: str) -> bool:
        if not model:
            return True
        if model in CODEX_VALID_MODELS:
            return True
        model_lower = model.lower()
        return any(k in model_lower for k in ["davinci", "cushman"])

    async def _call_claude_cli_async(self, prompt: str, model: Optional[str] = None) -> str:
        cmd = [self.claude_command, "--print"]
        if model:
            model_map = {
                "code-davinci-002": "davinci",
                "code-cushman-001": "cushman",
            }
            short_name = None
            for full_name, mapped in model_map.items():
                if full_name in model:
                    short_name = mapped
                    break
            if not short_name:
                model_lower = model.lower()
                for known in ["davinci", "cushman"]:
                    if known in model_lower:
                        short_name = known
                        break
            if short_name:
                cmd.extend(["--model", short_name])

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=prompt.encode("utf-8")),
                    timeout=120,
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                logger.error("Codex CLI timed out")
                raise Exception("Codex CLI timed out after 120 seconds")
            if proc.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="ignore") if stderr else "Unknown error"
                logger.error(f"Codex CLI returned non-zero: {proc.returncode}")
                raise Exception("Codex CLI error")
            response_text = stdout.decode("utf-8", errors="ignore").strip()
            if len(response_text) > MAX_PROMPT_LENGTH:
                logger.warning("Codex response truncated due to length")
                response_text = response_text[:MAX_PROMPT_LENGTH]
            return response_text
        except FileNotFoundError:
            logger.error("Codex CLI not found")
            raise Exception("Codex CLI not found. Please ensure 'codex' is installed and in PATH.")
        except Exception as e:
            logger.error(f"Error calling Codex: {type(e).__name__}")
            raise
