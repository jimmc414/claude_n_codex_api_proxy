"""Simple tests for Codex routing"""
from anthropic_router import create_client
from codex_client import CodexClient
from openai_router import AsyncOpenAIRouter
import pytest


def test_codex_detection():
    client = create_client(provider="codex", api_key="999999999")
    assert isinstance(client.client, CodexClient)


def test_openai_message_list_content_conversion(monkeypatch):
    router = create_client(provider="openai", api_key="test")
    captured = {}

    class DummyResp:
        def __init__(self):
            self.id = "resp_123"
            self.choices = [type("Choice", (), {"message": type("Msg", (), {"content": "ok"})()})]
            self.usage = type("Usage", (), {"prompt_tokens": 0, "completion_tokens": 0})()

    def fake_create(*, model, messages, max_tokens, temperature=None, stop=None):
        captured["messages"] = messages
        return DummyResp()

    monkeypatch.setattr(router.client.chat.completions, "create", fake_create)
    router.messages.create(
        model="gpt-test",
        max_tokens=5,
        messages=[{"role": "user", "content": [{"type": "text", "text": "Hello"}, {"type": "text", "text": " world"}]}],
    )
    assert captured["messages"][0]["content"] == "Hello world"


@pytest.mark.asyncio
async def test_openai_message_list_content_conversion_async(monkeypatch):
    router = AsyncOpenAIRouter(api_key="test")
    captured = {}

    class DummyResp:
        def __init__(self):
            self.id = "resp_123"
            self.choices = [type("Choice", (), {"message": type("Msg", (), {"content": "ok"})()})]
            self.usage = type("Usage", (), {"prompt_tokens": 0, "completion_tokens": 0})()

    async def fake_create(*, model, messages, max_tokens, temperature=None, stop=None):
        captured["messages"] = messages
        return DummyResp()

    monkeypatch.setattr(router.client.chat.completions, "create", fake_create)
    await router.messages.create(
        model="gpt-test",
        max_tokens=5,
        messages=[{"role": "user", "content": [{"type": "text", "text": "Hello"}, {"type": "text", "text": " world"}]}],
    )
    assert captured["messages"][0]["content"] == "Hello world"
