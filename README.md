# Claude & Codex API Router

A universal HTTP proxy and Python library that automatically routes Anthropic or OpenAI API calls to local CLI tools (Claude Code or Codex) when the API key is set to all 9s, otherwise uses the real cloud APIs.

## Two Solutions Included

### 1. Universal HTTP Proxy (Works with ANY language/tool)
An HTTP/HTTPS proxy server that intercepts Anthropic or OpenAI API calls from any application, regardless of programming language.

### 2. Python Library (Python-specific)
Drop-in replacements for the Anthropic and OpenAI Python clients that handle routing internally, routing to Claude Code or Codex when appropriate.

## Features

- **Universal Compatibility**: HTTP proxy works with ANY programming language or tool
- **Transparent Routing**: No code changes needed for existing projects (with proxy)
- **Claude Code & Codex Integration**: Automatically routes to local Claude Code or Codex CLI when API key is all 9s
- **API Compatibility**: Maintains Anthropic/OpenAI API response format
- **Easy Configuration**: Just set your API key to all 9s to enable local routing
- **Python Library**: Drop-in replacement clients for Anthropic and OpenAI Python SDKs
- **Async Support**: Includes both synchronous and asynchronous clients

## Installation

```bash
pip install -r requirements.txt
# On Windows you can also use: py -m pip install -r requirements.txt
```

Make sure you have the relevant CLI installed and available in your PATH:
```bash
claude --version   # for Claude Code
codex --version    # for Codex
```

## Quick Start

### Option 1: Universal HTTP Proxy (Recommended)

1. **Setup and start the proxy:**
```bash
python setup_proxy.py  # One-time setup
# macOS / Linux
./start_proxy.sh       # Start proxy server
# Windows
python start_proxy.py
```

2. **Configure your environment (examples):**

macOS/Linux (bash/zsh):
```bash
export HTTP_PROXY=http://localhost:8080
export HTTPS_PROXY=http://localhost:8080
export ANTHROPIC_API_KEY=999999999999   # All 9s for Claude Code
export OPENAI_API_KEY=999999999999      # All 9s for Codex
```

Windows (PowerShell):
```powershell
$env:HTTP_PROXY="http://localhost:8080"
$env:HTTPS_PROXY="http://localhost:8080"
$env:ANTHROPIC_API_KEY="999999999999"   # All 9s for Claude Code
$env:OPENAI_API_KEY="999999999999"      # All 9s for Codex
```

3. **Use from ANY language/tool:**
```bash
# Python, Node.js, cURL, etc - all work through the proxy!
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: 999999999999" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-sonnet-20240229","messages":[{"role":"user","content":"Hello"}],"max_tokens":50}'
```

## Allowing Additional API Endpoints

By default the proxy only permits a curated set of `/v1` API paths. The default
configuration covers common Anthropic and OpenAI endpoints and falls back to
allow any path under `/v1/`.

To permit other endpoints you can either override the entire allow-list or
extend it:

- **Override** with a comma-separated list via the `ALLOWED_PATHS` environment
  variable or `--allowed-paths` option:

  ```bash
  ALLOWED_PATHS="^/v1/my/endpoint$" python start_proxy.py
  # or
  python start_proxy.py --allowed-paths '^/v1/my/endpoint$'
  ```

- **Extend** the defaults by passing `--allowed-path` one or more times:

  ```bash
  python start_proxy.py --allowed-path '^/v1/beta$' --allowed-path '^/v1/other$'
  ```

Patterns are regular expressions that are combined at startup. This allows new
API endpoints to be exposed through the proxy without modifying the source
code.

### Option 2: Python Library

```python
from anthropic_router import create_client

# Use Codex locally
client = create_client(provider="codex", api_key="999999999999")

# Or use Claude Code locally
# client = create_client(provider="claude", api_key="999999999999")

# Or use cloud providers
# client = create_client(provider="anthropic", api_key="sk-ant-real-key")

message = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello, how are you?"}]
)

print(message.content[0].text)
```

Valid values for `provider` are `"claude"`, `"anthropic"`, `"codex"`, and `"openai"`. Passing any other value to `create_client` or via the `AI_ROUTER_DEFAULT` environment variable will raise a `ValueError`.

## How It Works

1. When you create a client with an API key that's all 9s (e.g., "999999999999"), the router automatically routes requests to the local Claude Code or Codex CLI
2. The router converts standard Anthropic/OpenAI API format to the respective local CLI format
3. Responses from the local CLI are converted back to the standard API format
4. Your code doesn't need to change—it behaves like the official Anthropic or OpenAI client

## Examples

See `example.py` for comprehensive examples including:
- Basic usage
- System prompts
- Multi-turn conversations
- Async operations
- Environment variable configuration

Run the examples:
```bash
python example.py
```

### Planning a Migration Away From Cloud API Keys?

If you need to adapt an existing application so it can call Claude Code or Codex
directly via the locally installed CLIs (e.g., Claude Max or ChatGPT Pro
subscriptions), read [`docs/direct_llm_integration.md`](docs/direct_llm_integration.md).
The guide explains how the proxy works, what preconditions must hold, and how to
translate API payloads into CLI prompts and back without ever storing API keys
in your codebase.

## Testing

Run the test suite to verify the routing works correctly:
```bash
pytest
```

## API Key Detection

The following API key formats will trigger local routing (Claude Code or Codex):
- `"999999999999"` - Pure 9s
- `"sk-ant-999999999999"` or `"sk-openai-999999999999"` - With standard prefix
- Any string where the last segment (after splitting by `-`) is all 9s

## Limitations

- Streaming is not yet supported when routing to Claude Code or Codex
- Token counting is approximate when using local CLI tools
- Some advanced API features may not be available through Claude Code or Codex

## Files

### Proxy Server (Universal)
- `proxy_server.py` - HTTP/HTTPS proxy server
- `claude_code_proxy_handler.py` - Proxy request handler for Claude Code
- `setup_proxy.py` - One-time setup script for proxy
- `start_proxy.sh` - Convenient proxy launcher script
- `start_proxy.py` - Cross-platform proxy launcher script
- `test_universal.py` - Tests for multiple languages/tools

### Python Library
- `anthropic_router.py` - Anthropic/Claude Code routing logic
- `openai_router.py` - OpenAI/Codex routing logic
- `claude_code_client.py` - Claude Code CLI interface
- `codex_client.py` - Codex CLI interface
- `example.py` - Python library usage examples
- `test_router.py` - Anthropic/Claude Code routing tests
- `test_openai_router.py` - OpenAI/Codex routing tests

### Common
- `requirements.txt` - Python dependencies
- `test_simple.py` - Simple proxy test
