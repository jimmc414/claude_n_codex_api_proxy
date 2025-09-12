import asyncio
import os
import sys
from pathlib import Path
import contextlib

import pytest

# Ensure repository root on path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from claude_code_client import ClaudeCodeClient
from codex_client import CodexClient
from claude_code_proxy_handler import ClaudeCodeProxyHandler
from codex_proxy_handler import CodexProxyHandler

SCRIPT = Path(__file__).with_name("hanging_cli.py")

async def _fast_timeout(awaitable, timeout, *args, **kwargs):
    task = asyncio.create_task(awaitable)
    await asyncio.sleep(0.05)
    task.cancel()
    with contextlib.suppress(BaseException):
        await task
    raise asyncio.TimeoutError

@pytest.mark.asyncio
@pytest.mark.parametrize("client_cls", [ClaudeCodeClient, CodexClient])
async def test_client_process_killed_on_timeout(client_cls, monkeypatch, tmp_path):
    pid_file = tmp_path / "pid"
    os.environ["PID_FILE"] = str(pid_file)
    client = client_cls()
    client.claude_command = str(SCRIPT)

    monkeypatch.setattr(asyncio, "wait_for", _fast_timeout)

    with pytest.raises(Exception):
        await client.acreate_message(
            messages=[{"role": "user", "content": "hi"}],
            model="test",
            max_tokens=1,
        )

    pid = int(pid_file.read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
    os.environ.pop("PID_FILE", None)

@pytest.mark.asyncio
@pytest.mark.parametrize("handler_cls", [ClaudeCodeProxyHandler, CodexProxyHandler])
async def test_handler_process_killed_on_timeout(handler_cls, monkeypatch, tmp_path):
    pid_file = tmp_path / "pid"
    os.environ["PID_FILE"] = str(pid_file)
    handler = handler_cls()
    handler.claude_command = str(SCRIPT)

    monkeypatch.setattr(asyncio, "wait_for", _fast_timeout)

    with pytest.raises(Exception):
        await handler._call_claude_cli_async("prompt")

    pid = int(pid_file.read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
    os.environ.pop("PID_FILE", None)
