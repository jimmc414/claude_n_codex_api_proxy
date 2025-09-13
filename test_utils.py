import pytest
import utils
from utils import (
    run_subprocess,
    run_subprocess_async,
    CLINotFoundError,
    CLITimeoutError,
    CLIError,
)


def test_is_all_nines_api_key_true_cases():
    assert utils.is_all_nines_api_key("999999")
    assert utils.is_all_nines_api_key("sk-ant-999")


def test_is_all_nines_api_key_false_cases():
    assert not utils.is_all_nines_api_key("123456")
    assert not utils.is_all_nines_api_key("sk-ant-123")
    assert not utils.is_all_nines_api_key(None)


def test_run_subprocess_not_found():
    with pytest.raises(CLINotFoundError):
        run_subprocess(["nonexistent_command"], "", "Test")


def test_run_subprocess_timeout():
    cmd = ["python", "-c", "import time; time.sleep(5)"]
    with pytest.raises(CLITimeoutError):
        run_subprocess(cmd, "", "Sleep", timeout=1)


def test_run_subprocess_error():
    cmd = ["python", "-c", "import sys; sys.exit(1)"]
    with pytest.raises(CLIError):
        run_subprocess(cmd, "", "Fail")


@pytest.mark.asyncio
async def test_run_subprocess_async_not_found():
    with pytest.raises(CLINotFoundError):
        await run_subprocess_async(["nonexistent_command"], "", "Test")


@pytest.mark.asyncio
async def test_run_subprocess_async_timeout():
    cmd = ["python", "-c", "import time; time.sleep(5)"]
    with pytest.raises(CLITimeoutError):
        await run_subprocess_async(cmd, "", "Sleep", timeout=1)


@pytest.mark.asyncio
async def test_run_subprocess_async_error():
    cmd = ["python", "-c", "import sys; sys.exit(1)"]
    with pytest.raises(CLIError):
        await run_subprocess_async(cmd, "", "Fail")
