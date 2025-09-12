import pytest
import openai_router
from openai_router import OpenAIRouter, AsyncOpenAIRouter


def test_stop_sequences_passed_to_openai(monkeypatch):
    captured = {}

    class MockResponse:
        id = "resp"

        class Choice:
            def __init__(self):
                self.message = {"content": "hello"}

        choices = [Choice()]

        class Usage:
            prompt_tokens = 0
            completion_tokens = 0

        usage = Usage()

    class MockChatCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return MockResponse()

    class MockChat:
        def __init__(self):
            self.completions = MockChatCompletions()

    class MockClient:
        def __init__(self, *args, **kwargs):
            self.chat = MockChat()

    monkeypatch.setattr(openai_router, "OpenAI", lambda api_key=None: MockClient())
    router = OpenAIRouter(api_key="real-key")
    router.messages.create(
        model="gpt-4",
        max_tokens=5,
        messages=[{"role": "user", "content": "hi"}],
        stop_sequences=["END"],
    )
    assert captured["stop"] == ["END"]


def test_async_stop_sequences_passed_to_openai(monkeypatch):
    captured = {}

    class MockResponse:
        id = "resp"

        class Choice:
            def __init__(self):
                self.message = {"content": "hello"}

        choices = [Choice()]

        class Usage:
            prompt_tokens = 0
            completion_tokens = 0

        usage = Usage()

    class MockChatCompletions:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return MockResponse()

    class MockChat:
        def __init__(self):
            self.completions = MockChatCompletions()

    class MockClient:
        def __init__(self, *args, **kwargs):
            self.chat = MockChat()

    monkeypatch.setattr(openai_router, "AsyncOpenAI", lambda api_key=None: MockClient())
    router = AsyncOpenAIRouter(api_key="real-key")

    async def run():
        await router.messages.create(
            model="gpt-4",
            max_tokens=5,
            messages=[{"role": "user", "content": "hi"}],
            stop_sequences=["END"],
        )

    import asyncio

    asyncio.run(run())
    assert captured["stop"] == ["END"]
