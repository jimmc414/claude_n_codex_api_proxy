import pytest
import openai_router
from openai_router import OpenAIRouter, AsyncOpenAIRouter


def test_stop_sequences_passed_to_openai(monkeypatch):
    captured = {}

    class MockResponse:
        id = "resp"

        class Choice:
            def __init__(self):
                self.message = type("Msg", (), {"content": "hello"})()

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
                self.message = type("Msg", (), {"content": "hello"})()

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


def test_stream_passed_to_openai(monkeypatch):
    captured = {}

    class MockChunk:
        id = "resp_stream"

        class Choice:
            def __init__(self):
                self.delta = type("Delta", (), {"content": "hello"})()

        choices = [Choice()]

        class Usage:
            prompt_tokens = 0
            completion_tokens = 0

        usage = Usage()

    class MockStreamResponse:
        def __iter__(self):
            return iter([MockChunk()])

    class MockChatCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return MockStreamResponse()

    class MockChat:
        def __init__(self):
            self.completions = MockChatCompletions()

    class MockClient:
        def __init__(self, *args, **kwargs):
            self.chat = MockChat()

    monkeypatch.setattr(openai_router, "OpenAI", lambda api_key=None: MockClient())
    router = OpenAIRouter(api_key="real-key")
    msg = router.messages.create(
        model="gpt-4",
        max_tokens=5,
        messages=[{"role": "user", "content": "hi"}],
        stream=True,
    )
    assert captured["stream"] is True
    assert msg.content[0].text == "hello"


def test_empty_stream_raises_error(monkeypatch):
    class MockStreamResponse:
        def __iter__(self):
            return iter([])

    class MockChatCompletions:
        def create(self, **kwargs):
            return MockStreamResponse()

    class MockChat:
        def __init__(self):
            self.completions = MockChatCompletions()

    class MockClient:
        def __init__(self, *args, **kwargs):
            self.chat = MockChat()

    monkeypatch.setattr(openai_router, "OpenAI", lambda api_key=None: MockClient())
    router = OpenAIRouter(api_key="real-key")
    with pytest.raises(RuntimeError, match="No chunks were received"):
        router.messages.create(
            model="gpt-4",
            max_tokens=5,
            messages=[{"role": "user", "content": "hi"}],
            stream=True,
        )


def test_sampling_params_and_metadata_passed_to_openai(monkeypatch):
    captured = {}

    class MockResponse:
        id = "resp"

        class Choice:
            def __init__(self):
                self.message = type("Msg", (), {"content": "ok"})()

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
        top_p=0.9,
        top_k=40,
        metadata={"foo": "bar"},
    )
    assert captured["top_p"] == 0.9
    assert "top_k" not in captured
    # metadata is Anthropic-specific and should not be passed to OpenAI API
    assert "metadata" not in captured


def test_async_stream_passed_to_openai(monkeypatch):
    captured = {}

    class MockChunk:
        id = "resp_stream"

        class Choice:
            def __init__(self):
                self.delta = type("Delta", (), {"content": "hello"})()

        choices = [Choice()]

        class Usage:
            prompt_tokens = 0
            completion_tokens = 0

        usage = Usage()

    class MockStreamResponse:
        def __aiter__(self):
            async def gen():
                yield MockChunk()
            return gen()

    class MockChatCompletions:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return MockStreamResponse()

    class MockChat:
        def __init__(self):
            self.completions = MockChatCompletions()

    class MockClient:
        def __init__(self, *args, **kwargs):
            self.chat = MockChat()

    monkeypatch.setattr(openai_router, "AsyncOpenAI", lambda api_key=None: MockClient())
    router = AsyncOpenAIRouter(api_key="real-key")

    async def run():
        return await router.messages.create(
            model="gpt-4",
            max_tokens=5,
            messages=[{"role": "user", "content": "hi"}],
            stream=True,
        )

    import asyncio

    msg = asyncio.run(run())
    assert captured["stream"] is True
    assert msg.content[0].text == "hello"


def test_async_empty_stream_raises_error(monkeypatch):
    class MockStreamResponse:
        def __aiter__(self):
            async def gen():
                if False:
                    yield None
            return gen()

    class MockChatCompletions:
        async def create(self, **kwargs):
            return MockStreamResponse()

    class MockChat:
        def __init__(self):
            self.completions = MockChatCompletions()

    class MockClient:
        def __init__(self, *args, **kwargs):
            self.chat = MockChat()

    monkeypatch.setattr(openai_router, "AsyncOpenAI", lambda api_key=None: MockClient())
    router = AsyncOpenAIRouter(api_key="real-key")

    async def run():
        with pytest.raises(RuntimeError, match="No chunks were received"):
            await router.messages.create(
                model="gpt-4",
                max_tokens=5,
                messages=[{"role": "user", "content": "hi"}],
                stream=True,
            )

    import asyncio

    asyncio.run(run())


def test_async_sampling_params_and_metadata_passed_to_openai(monkeypatch):
    captured = {}

    class MockResponse:
        id = "resp"

        class Choice:
            def __init__(self):
                self.message = type("Msg", (), {"content": "ok"})()

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
            top_p=0.9,
            top_k=40,
            metadata={"foo": "bar"},
        )

    import asyncio

    asyncio.run(run())
    assert captured["top_p"] == 0.9
    assert "top_k" not in captured
    # metadata is Anthropic-specific and should not be passed to OpenAI API
    assert "metadata" not in captured


def test_dict_content_normalization(monkeypatch):
    captured = {}

    class MockResponse:
        id = "resp"

        class Choice:
            def __init__(self):
                self.message = type("Msg", (), {"content": "ok"})()

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
        messages=[
            {"role": "user", "content": {"type": "text", "text": "hello"}},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "foo"},
                    {"type": "image", "url": "http://"},
                    {"type": "text", "text": "bar"},
                ],
            },
        ],
    )
    assert captured["messages"][0]["content"] == "hello"
    assert (
        captured["messages"][1]["content"]
        == "foo [image content] bar"
    )
    for msg in captured["messages"]:
        assert isinstance(msg["content"], str)


def test_async_dict_content_normalization(monkeypatch):
    captured = {}

    class MockResponse:
        id = "resp"

        class Choice:
            def __init__(self):
                self.message = type("Msg", (), {"content": "ok"})()

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
            messages=[
                {"role": "user", "content": {"type": "text", "text": "hello"}},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "foo"},
                        {"type": "image", "url": "http://"},
                        {"type": "text", "text": "bar"},
                    ],
                },
            ],
        )

    import asyncio

    asyncio.run(run())
    assert captured["messages"][0]["content"] == "hello"
    assert (
        captured["messages"][1]["content"]
        == "foo [image content] bar"
    )
    for msg in captured["messages"]:
        assert isinstance(msg["content"], str)
