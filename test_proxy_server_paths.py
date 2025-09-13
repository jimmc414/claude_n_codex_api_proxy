import proxy_server

class DummyRequest:
    def __init__(self, path, method="POST", content=b""):
        self.path = path
        self.method = method
        self.content = content

class DummyFlow:
    def __init__(self, path, method="POST", content=b""):
        self.request = DummyRequest(path, method, content)


def test_openai_endpoints_allowed():
    interceptor = proxy_server.AIInterceptor()
    for path in ["/v1/chat/completions", "/v1/completions"]:
        flow = DummyFlow(path)
        assert interceptor._validate_request(flow) is None, f"{path} should be allowed"


def test_fallback_allows_new_paths():
    interceptor = proxy_server.AIInterceptor()
    flow = DummyFlow("/v1/new/endpoint")
    assert interceptor._validate_request(flow) is None, "Fallback /v1/* pattern should allow new endpoint"


def test_custom_paths_override():
    original = proxy_server.ALLOWED_PATHS_REGEX
    try:
        proxy_server.ALLOWED_PATHS_REGEX = proxy_server.build_allowed_paths_regex([r'^/custom$'])
        interceptor = proxy_server.AIInterceptor()
        assert interceptor._validate_request(DummyFlow("/custom")) is None
        assert interceptor._validate_request(DummyFlow("/v1/completions"))["error"]["type"] == "not_found"
    finally:
        proxy_server.ALLOWED_PATHS_REGEX = original
