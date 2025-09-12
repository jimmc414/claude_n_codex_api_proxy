# Claude Code API Router

A universal HTTP proxy and Python library that automatically routes Anthropic API calls to Claude Code (local inference) when the API key is set to all 9s, otherwise uses the standard Anthropic API.

## Two Solutions Included

### 1. Universal HTTP Proxy (Works with ANY language/tool)
An HTTP/HTTPS proxy server that intercepts all Anthropic API calls from any application, regardless of programming language.

### 2. Python Library (Python-specific)
A drop-in replacement for the Anthropic Python client that handles routing internally.

## Features

- **Universal Compatibility**: HTTP proxy works with ANY programming language or tool
- **Transparent Routing**: No code changes needed for existing projects (with proxy)
- **Claude Code Integration**: Automatically routes to local Claude Code CLI when API key is all 9s
- **API Compatibility**: Maintains full Anthropic API response format
- **Easy Configuration**: Just set your API key to all 9s to enable local routing
- **Python Library**: Drop-in replacement for Anthropic Python client
- **Async Support**: Includes both synchronous and asynchronous clients

## Installation

```bash
pip install -r requirements.txt
```

Make sure you have Claude Code CLI installed and available in your PATH:
```bash
claude --version
```

## Quick Start

### Option 1: Universal HTTP Proxy (Recommended)

1. **Setup and start the proxy:**
```bash
python setup_proxy.py  # One-time setup
./start_proxy.sh       # Start proxy server
```

2. **Configure your environment:**
```bash
export HTTP_PROXY=http://localhost:8080
export HTTPS_PROXY=http://localhost:8080
export ANTHROPIC_API_KEY=999999999999  # All 9s for Claude Code
```

3. **Use from ANY language/tool:**
```bash
# Python, Node.js, cURL, etc - all work through the proxy!
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: 999999999999" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-sonnet-20240229","messages":[{"role":"user","content":"Hello"}],"max_tokens":50}'
```

### Option 2: Python Library

```python
from anthropic_router import create_client

# Use Claude Code (local inference)
client = create_client(api_key="999999999999")

# Or use the real Anthropic API
# client = create_client(api_key="sk-ant-api03-your-real-key")

message = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(message.content[0].text)
```

## How It Works

1. When you create a client with an API key that's all 9s (e.g., "999999999999"), the router automatically detects this and routes all API calls to Claude Code CLI
2. The router converts Anthropic API format to Claude Code CLI format
3. Responses from Claude Code are converted back to Anthropic API format
4. Your code doesn't need to change - it works exactly like the standard Anthropic client

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

## Testing

Run the test suite to verify the routing works correctly:
```bash
python test_router.py
```

## API Key Detection

The following API key formats will trigger Claude Code routing:
- `"999999999999"` - Pure 9s
- `"sk-ant-999999999999"` - With standard prefix
- Any string where the last segment (after splitting by `-`) is all 9s

## Limitations

- Streaming is not yet supported when routing to Claude Code
- Token counting is approximate when using Claude Code
- Some advanced Anthropic API features may not be available through Claude Code

## Files

### Proxy Server (Universal)
- `proxy_server.py` - HTTP/HTTPS proxy server
- `claude_code_proxy_handler.py` - Proxy request handler for Claude Code
- `setup_proxy.py` - One-time setup script for proxy
- `start_proxy.sh` - Convenient proxy launcher script
- `test_universal.py` - Tests for multiple languages/tools

### Python Library
- `anthropic_router.py` - Python client routing logic
- `claude_code_client.py` - Claude Code CLI interface
- `example.py` - Python library usage examples
- `test_router.py` - Python library test suite

### Common
- `requirements.txt` - Python dependencies
- `test_simple.py` - Simple proxy test