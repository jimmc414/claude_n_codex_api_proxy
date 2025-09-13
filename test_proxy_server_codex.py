import json
import pytest
import proxy_server

DEFAULT_REGEX = proxy_server.build_allowed_paths_regex(
    proxy_server.DEFAULT_ALLOWED_PATH_PATTERNS
)


class DummyRequest:
    def __init__(self, path, method="POST", content=b"{}"):
        self.path = path
        self.method = method
        self.content = content


class DummyFlow:
    def __init__(self, path, method="POST", content=b"{}"):
        self.request = DummyRequest(path, method, content)
        self.response = None


@pytest.mark.asyncio
async def test_chat_completions_success(monkeypatch):
    interceptor = proxy_server.AIInterceptor(DEFAULT_REGEX)

    async def mock_messages(data, method):
        return {"id": "1"}

    monkeypatch.setattr(interceptor.codex_handler, "handle_messages_request", mock_messages)

    body = json.dumps({"messages": [{"role": "user", "content": "hi"}]})
    flow = DummyFlow("/v1/chat/completions", content=body.encode())
    await interceptor._handle_codex_request(flow)
    assert flow.response.status_code == 200


@pytest.mark.asyncio
async def test_chat_completions_not_found(monkeypatch):
    interceptor = proxy_server.AIInterceptor(DEFAULT_REGEX)

    async def mock_messages(data, method):
        return {"error": {"type": "not_found_error", "message": "missing"}}

    monkeypatch.setattr(interceptor.codex_handler, "handle_messages_request", mock_messages)

    body = json.dumps({"messages": []})
    flow = DummyFlow("/v1/chat/completions", content=body.encode())
    await interceptor._handle_codex_request(flow)
    assert flow.response.status_code == 404


@pytest.mark.asyncio
async def test_completions_success(monkeypatch):
    interceptor = proxy_server.AIInterceptor(DEFAULT_REGEX)

    async def mock_complete(data, method):
        return {"completion": "ok"}

    monkeypatch.setattr(interceptor.codex_handler, "handle_complete_request", mock_complete)

    body = json.dumps({"prompt": "hi"})
    flow = DummyFlow("/v1/completions", content=body.encode())
    await interceptor._handle_codex_request(flow)
    assert flow.response.status_code == 200


@pytest.mark.asyncio
async def test_completions_invalid(monkeypatch):
    interceptor = proxy_server.AIInterceptor(DEFAULT_REGEX)

    async def mock_complete(data, method):
        return {"error": {"type": "invalid_request_error", "message": "bad"}}

    monkeypatch.setattr(interceptor.codex_handler, "handle_complete_request", mock_complete)

    body = json.dumps({"prompt": "hi"})
    flow = DummyFlow("/v1/completions", content=body.encode())
    await interceptor._handle_codex_request(flow)
    assert flow.response.status_code == 400
