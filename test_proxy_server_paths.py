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
