import asyncio
import subprocess
from typing import Optional, List


class CLIError(Exception):
    """Base exception for CLI-related issues."""


class CLINotFoundError(CLIError):
    """Raised when the CLI executable is not found."""


class CLITimeoutError(CLIError):
    """Raised when the CLI command times out."""


def is_all_nines_api_key(api_key: Optional[str]) -> bool:
    """Return True if the API key (after removing any prefix) is all 9s."""
    if not api_key:
        return False
    key_part = api_key.split('-')[-1] if '-' in api_key else api_key
    return all(c == '9' for c in key_part)


def run_subprocess(cmd: List[str], input_text: str, name: str, *, timeout: int = 120,
                   include_stderr: bool = True) -> str:
    """Run a subprocess command with timeout handling."""
    try:
        result = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise CLITimeoutError(f"{name} CLI timed out after {timeout} seconds")
    except FileNotFoundError:
        raise CLINotFoundError(
            f"{name} CLI not found. Please ensure '{cmd[0]}' is installed and in PATH"
        )
    except Exception as e:
        raise CLIError(f"Error calling {name}: {str(e)}")

    if result.returncode != 0:
        error_msg = result.stderr or "Unknown error"
        if include_stderr:
            raise CLIError(f"{name} CLI error: {error_msg}")
        raise CLIError(f"{name} CLI error")

    return result.stdout.strip()


async def run_subprocess_async(cmd: List[str], input_text: str, name: str, *, timeout: int = 120,
                                include_stderr: bool = True) -> str:
    """Run a subprocess command asynchronously with timeout handling."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        raise CLINotFoundError(
            f"{name} CLI not found. Please ensure '{cmd[0]}' is installed and in PATH"
        )

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=input_text.encode()), timeout=timeout
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        raise CLITimeoutError(f"{name} CLI timed out after {timeout} seconds")

    if proc.returncode != 0:
        error_msg = stderr.decode() if stderr else "Unknown error"
        if include_stderr:
            raise CLIError(f"{name} CLI error: {error_msg}")
        raise CLIError(f"{name} CLI error")

    return stdout.decode().strip()
