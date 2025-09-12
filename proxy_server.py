#!/usr/bin/env python3
"""
HTTP/HTTPS Proxy Server for Anthropic API interception.
Routes to Claude Code when API key is all 9s.
FIXED VERSION with security improvements and bug fixes.
"""
import asyncio
import json
import logging
import sys
import re
from typing import Optional, Dict, Any
from mitmproxy import http, options
from mitmproxy.tools.dump import DumpMaster
from claude_code_proxy_handler import ClaudeCodeProxyHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for security
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB max request size
MAX_PROMPT_LENGTH = 100000  # Max characters in prompt
ALLOWED_METHODS = {'GET', 'POST', 'OPTIONS'}
ALLOWED_PATHS_REGEX = re.compile(r'^/v1/(messages|complete|models)/?.*$')


class AnthropicInterceptor:
    """
    Mitmproxy addon that intercepts Anthropic API calls and routes them
    to Claude Code when the API key is all 9s.
    """
    
    def __init__(self):
        self.claude_handler = ClaudeCodeProxyHandler()
        self.stats = {
            'total_requests': 0,
            'claude_code_routed': 0,
            'anthropic_forwarded': 0,
            'errors': 0,
            'blocked_requests': 0
        }
    
    def _is_all_nines(self, api_key: str) -> bool:
        """Check if API key is all 9s (indicating Claude Code routing)."""
        if not api_key or len(api_key) > 200:  # Sanity check on key length
            return False
        # Remove common prefixes safely
        key_parts = api_key.split('-')
        if len(key_parts) > 10:  # Prevent DoS with many splits
            return False
        key_part = key_parts[-1] if key_parts else api_key
        # Check if all characters are 9s (limit check to prevent DoS)
        return len(key_part) > 0 and len(key_part) < 100 and all(c == '9' for c in key_part)
    
    def _is_anthropic_request(self, flow: http.HTTPFlow) -> bool:
        """Check if this is a request to Anthropic API."""
        host = flow.request.pretty_host.lower()
        return host in ['api.anthropic.com', 'anthropic.com']
    
    def _validate_request(self, flow: http.HTTPFlow) -> Optional[Dict[str, Any]]:
        """Validate and sanitize the request."""
        # Check method
        if flow.request.method not in ALLOWED_METHODS:
            return {
                "error": {
                    "type": "method_not_allowed",
                    "message": f"Method {flow.request.method} not allowed"
                }
            }
        
        # Check path
        if not ALLOWED_PATHS_REGEX.match(flow.request.path):
            return {
                "error": {
                    "type": "not_found",
                    "message": f"Path {flow.request.path} not found"
                }
            }
        
        # Check request size
        if flow.request.content and len(flow.request.content) > MAX_REQUEST_SIZE:
            return {
                "error": {
                    "type": "request_too_large",
                    "message": f"Request size exceeds maximum of {MAX_REQUEST_SIZE} bytes"
                }
            }
        
        return None
    
    async def request(self, flow: http.HTTPFlow) -> None:
        """Handle intercepted HTTP requests."""
        if not self._is_anthropic_request(flow):
            return
        
        self.stats['total_requests'] += 1
        
        # Validate request
        validation_error = self._validate_request(flow)
        if validation_error:
            self.stats['blocked_requests'] += 1
            flow.response = http.Response.make(
                400,
                json.dumps(validation_error),
                {"Content-Type": "application/json"}
            )
            return
        
        # Extract API key from headers (with size limits)
        api_key = ''
        x_api_key = flow.request.headers.get('x-api-key', '')
        if x_api_key and len(x_api_key) < 500:
            api_key = x_api_key
        
        if not api_key:
            # Try Authorization header as fallback
            auth_header = flow.request.headers.get('authorization', '')
            if auth_header and len(auth_header) < 500 and auth_header.startswith('Bearer '):
                api_key = auth_header[7:]
        
        # Check if we should route to Claude Code
        if self._is_all_nines(api_key):
            logger.info(f"🔀 Routing to Claude Code: {flow.request.method} {flow.request.path}")
            self.stats['claude_code_routed'] += 1
            await self._handle_claude_code_request(flow)
        else:
            logger.info(f"➡️  Forwarding to Anthropic API: {flow.request.method} {flow.request.path}")
            self.stats['anthropic_forwarded'] += 1
            # Let the request pass through to the real Anthropic API
    
    async def _handle_claude_code_request(self, flow: http.HTTPFlow) -> None:
        """Route the request to Claude Code and return the response."""
        try:
            # Parse request body with size check
            request_data = {}
            if flow.request.content:
                if len(flow.request.content) > MAX_REQUEST_SIZE:
                    flow.response = http.Response.make(
                        413,
                        json.dumps({"error": {"type": "request_too_large", "message": "Request body too large"}}),
                        {"Content-Type": "application/json"}
                    )
                    return
                
                try:
                    content_str = flow.request.content.decode('utf-8', errors='ignore')
                    request_data = json.loads(content_str)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.error(f"Failed to parse request: {e}")
                    flow.response = http.Response.make(
                        400,
                        json.dumps({"error": {"type": "invalid_request", "message": "Invalid JSON in request body"}}),
                        {"Content-Type": "application/json"}
                    )
                    return
            
            # Validate request data structure
            if not isinstance(request_data, dict):
                flow.response = http.Response.make(
                    400,
                    json.dumps({"error": {"type": "invalid_request", "message": "Request body must be a JSON object"}}),
                    {"Content-Type": "application/json"}
                )
                return
            
            # Initialize status_code properly
            status_code = 404
            response_data = {}
            
            # Route to appropriate handler based on path
            path = flow.request.path.lower()
            if '/v1/messages' in path:
                response_data = await self.claude_handler.handle_messages_request(
                    request_data,
                    flow.request.method
                )
            elif '/v1/complete' in path:
                response_data = await self.claude_handler.handle_complete_request(
                    request_data,
                    flow.request.method
                )
            elif '/v1/models' in path and flow.request.method == 'GET':
                # Handle models endpoint
                response_data = {
                    "data": [
                        {"id": "claude-3-opus-20240229", "object": "model"},
                        {"id": "claude-3-sonnet-20240229", "object": "model"},
                        {"id": "claude-3-haiku-20240307", "object": "model"}
                    ]
                }
            else:
                response_data = {
                    "error": {
                        "type": "not_found_error",
                        "message": f"Endpoint {flow.request.path} not supported in Claude Code mode"
                    }
                }
            
            # Determine status code based on response
            if 'error' in response_data:
                error_type = response_data.get('error', {}).get('type', '')
                if 'not_found' in error_type:
                    status_code = 404
                elif 'invalid' in error_type or 'request' in error_type:
                    status_code = 400
                elif 'unauthorized' in error_type:
                    status_code = 401
                else:
                    status_code = 500
            else:
                status_code = 200
            
            # Create response with proper headers
            response_json = json.dumps(response_data)
            flow.response = http.Response.make(
                status_code,
                response_json,
                {
                    "Content-Type": "application/json",
                    "Content-Length": str(len(response_json))
                }
            )
            
        except asyncio.TimeoutError:
            logger.error("Claude Code request timed out")
            self.stats['errors'] += 1
            flow.response = http.Response.make(
                504,
                json.dumps({"error": {"type": "timeout_error", "message": "Request timed out"}}),
                {"Content-Type": "application/json"}
            )
        except Exception as e:
            logger.error(f"Error handling Claude Code request: {e}", exc_info=True)
            self.stats['errors'] += 1
            # Don't expose internal error details
            flow.response = http.Response.make(
                500,
                json.dumps({"error": {"type": "internal_error", "message": "An internal error occurred"}}),
                {"Content-Type": "application/json"}
            )
    
    def response(self, flow: http.HTTPFlow) -> None:
        """Handle responses (for logging/stats)."""
        if self._is_anthropic_request(flow) and flow.response:
            status = flow.response.status_code
            if status >= 400:
                self.stats['errors'] += 1
            
            # Log response status
            emoji = "✅" if status < 400 else "❌"
            logger.info(f"{emoji} Response: {status} for {flow.request.path}")
    
    def done(self) -> None:
        """Called when the proxy is shutting down."""
        logger.info("\n📊 Proxy Statistics:")
        logger.info(f"  Total requests: {self.stats['total_requests']}")
        logger.info(f"  Routed to Claude Code: {self.stats['claude_code_routed']}")
        logger.info(f"  Forwarded to Anthropic: {self.stats['anthropic_forwarded']}")
        logger.info(f"  Blocked requests: {self.stats['blocked_requests']}")
        logger.info(f"  Errors: {self.stats['errors']}")


async def start_proxy(host: str = "127.0.0.1", port: int = 8080):
    """Start the mitmproxy server."""
    # Validate host and port
    if not re.match(r'^[\d.]+$|^localhost$|^[\da-fA-F:]+$', host):
        raise ValueError(f"Invalid host: {host}")
    if not 1 <= port <= 65535:
        raise ValueError(f"Invalid port: {port}")
    
    # Configure mitmproxy options
    opts = options.Options(
        listen_host=host,
        listen_port=port,
        ssl_insecure=True,  # Accept any cert for upstream
    )
    
    # Create master with our interceptor
    master = DumpMaster(opts)
    master.addons.add(AnthropicInterceptor())
    
    logger.info(f"""
╔══════════════════════════════════════════════════════════╗
║          Anthropic API Proxy Server Started!              ║
╠══════════════════════════════════════════════════════════╣
║  Proxy URL: http://{host}:{port:<5}                          ║
║                                                            ║
║  Configure your application to use this proxy:            ║
║  • HTTP_PROXY=http://{host}:{port:<5}                        ║
║  • HTTPS_PROXY=http://{host}:{port:<5}                       ║
║                                                            ║
║  API keys with all 9s will route to Claude Code           ║
║  Other API keys will forward to Anthropic API             ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        await master.run()
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down proxy server...")
        master.shutdown()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Anthropic API Proxy Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on (default: 8080)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        asyncio.run(start_proxy(args.host, args.port))
    except KeyboardInterrupt:
        logger.info("\nProxy server stopped.")
        sys.exit(0)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()