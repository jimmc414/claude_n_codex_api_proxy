"""
Claude Code Proxy Handler - Handles API requests routed through the proxy.
FIXED VERSION with security improvements and input validation.
"""
import json
import shlex
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid
import logging
import re
from utils import (
    run_subprocess_async,
    CLINotFoundError,
    CLITimeoutError,
    CLIError,
)

logger = logging.getLogger(__name__)

# Security constants
MAX_PROMPT_LENGTH = 100000  # Maximum prompt length
MAX_MESSAGE_COUNT = 100  # Maximum number of messages
MAX_MESSAGE_LENGTH = 50000  # Maximum length per message
VALID_MODELS = {
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229", 
    "claude-3-haiku-20240307",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    "claude-2.1",
    "claude-2.0",
    "claude-instant-1.2"
}


class ClaudeCodeProxyHandler:
    """
    Handles Anthropic API requests that need to be routed to Claude Code.
    Converts HTTP API requests to Claude Code CLI calls and back.
    """
    
    def __init__(self):
        self.claude_command = "claude"
    
    def _validate_messages(self, messages: List[Dict]) -> Optional[str]:
        """Validate messages array for security and correctness."""
        if not isinstance(messages, list):
            return "Messages must be an array"
        
        if len(messages) == 0:
            return "Messages array cannot be empty"
        
        if len(messages) > MAX_MESSAGE_COUNT:
            return f"Too many messages (max {MAX_MESSAGE_COUNT})"
        
        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                return f"Message {i} must be an object"
            
            role = msg.get("role")
            if role not in ["user", "assistant", "system"]:
                return f"Message {i} has invalid role: {role}"
            
            content = msg.get("content")
            if content is None:
                return f"Message {i} missing content"
            
            # Check content length
            content_str = str(content) if not isinstance(content, str) else content
            if len(content_str) > MAX_MESSAGE_LENGTH:
                return f"Message {i} content too long (max {MAX_MESSAGE_LENGTH} chars)"
        
        return None
    
    def _validate_model(self, model: str) -> bool:
        """Validate model name against allowed models."""
        if not model:
            return True  # Use default if not specified
        
        # Check if it's a known model or contains known model names
        if model in VALID_MODELS:
            return True
        
        # Check for partial matches (e.g., custom model names containing standard ones)
        model_lower = model.lower()
        known_types = ["opus", "sonnet", "haiku", "claude-2", "claude-instant"]
        return any(known_type in model_lower for known_type in known_types)
    
    async def handle_messages_request(self, request_data: Dict[str, Any], method: str) -> Dict[str, Any]:
        """
        Handle /v1/messages endpoint requests.
        This is the main chat completion endpoint for Anthropic API.
        """
        if method != 'POST':
            return {
                "error": {
                    "type": "invalid_request_error",
                    "message": f"Method {method} not allowed for /v1/messages"
                }
            }
        
        try:
            # Validate request structure
            if not isinstance(request_data, dict):
                return {
                    "error": {
                        "type": "invalid_request_error",
                        "message": "Request body must be a JSON object"
                    }
                }
            
            # Extract and validate parameters
            messages = request_data.get('messages', [])
            validation_error = self._validate_messages(messages)
            if validation_error:
                return {
                    "error": {
                        "type": "invalid_request_error",
                        "message": validation_error
                    }
                }
            
            model = request_data.get('model', 'claude-3-sonnet-20240229')
            if not self._validate_model(model):
                return {
                    "error": {
                        "type": "invalid_request_error",
                        "message": f"Invalid or unsupported model: {model}"
                    }
                }
            
            max_tokens = request_data.get('max_tokens', 1024)
            if not isinstance(max_tokens, int) or max_tokens < 1 or max_tokens > 100000:
                return {
                    "error": {
                        "type": "invalid_request_error",
                        "message": "max_tokens must be between 1 and 100000"
                    }
                }
            
            system = request_data.get('system')
            if system and (not isinstance(system, str) or len(system) > MAX_MESSAGE_LENGTH):
                return {
                    "error": {
                        "type": "invalid_request_error",
                        "message": "System prompt too long or invalid"
                    }
                }
            
            temperature = request_data.get('temperature')
            if temperature is not None:
                if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
                    return {
                        "error": {
                            "type": "invalid_request_error",
                            "message": "temperature must be between 0 and 2"
                        }
                    }
            
            stream = request_data.get('stream', False)
            if stream:
                return {
                    "error": {
                        "type": "invalid_request_error",
                        "message": "Streaming is not supported in Claude Code mode"
                    }
                }
            
            # Format messages for Claude Code
            prompt = self._format_messages_for_claude(messages, system)
            
            # Check total prompt length
            if len(prompt) > MAX_PROMPT_LENGTH:
                return {
                    "error": {
                        "type": "invalid_request_error",
                        "message": f"Total prompt too long (max {MAX_PROMPT_LENGTH} chars)"
                    }
                }
            
            # Call Claude Code CLI
            response_text = await self._call_claude_cli_async(prompt, model)
            
            # Build response in Anthropic API format
            response = {
                "id": f"msg_{uuid.uuid4().hex[:12]}",
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": response_text
                    }
                ],
                "model": model,
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {
                    "input_tokens": len(prompt.split()),  # Rough estimate
                    "output_tokens": len(response_text.split())  # Rough estimate
                }
            }
            
            return response
            
        except CLINotFoundError as e:
            return {
                "error": {
                    "type": "not_found_error",
                    "message": str(e),
                }
            }
        except CLITimeoutError as e:
            return {
                "error": {
                    "type": "timeout_error",
                    "message": str(e),
                }
            }
        except CLIError as e:
            logger.error(f"Error handling messages request: {e}", exc_info=True)
            return {
                "error": {
                    "type": "api_error",
                    "message": str(e),
                }
            }
        except Exception as e:
            logger.error(f"Error handling messages request: {e}", exc_info=True)
            return {
                "error": {
                    "type": "api_error",
                    "message": "Failed to process request",
                }
            }
    
    async def handle_complete_request(self, request_data: Dict[str, Any], method: str) -> Dict[str, Any]:
        """
        Handle /v1/complete endpoint requests (legacy completion endpoint).
        """
        if method != 'POST':
            return {
                "error": {
                    "type": "invalid_request_error",
                    "message": f"Method {method} not allowed for /v1/complete"
                }
            }
        
        try:
            # Validate request structure
            if not isinstance(request_data, dict):
                return {
                    "error": {
                        "type": "invalid_request_error",
                        "message": "Request body must be a JSON object"
                    }
                }
            
            # Extract and validate parameters
            prompt = request_data.get('prompt', '')
            if not isinstance(prompt, str):
                return {
                    "error": {
                        "type": "invalid_request_error",
                        "message": "Prompt must be a string"
                    }
                }
            
            if len(prompt) > MAX_PROMPT_LENGTH:
                return {
                    "error": {
                        "type": "invalid_request_error",
                        "message": f"Prompt too long (max {MAX_PROMPT_LENGTH} chars)"
                    }
                }
            
            model = request_data.get('model', 'claude-3-sonnet-20240229')
            if not self._validate_model(model):
                return {
                    "error": {
                        "type": "invalid_request_error",
                        "message": f"Invalid or unsupported model: {model}"
                    }
                }
            
            max_tokens = request_data.get('max_tokens_to_sample', 1024)
            if not isinstance(max_tokens, int) or max_tokens < 1 or max_tokens > 100000:
                return {
                    "error": {
                        "type": "invalid_request_error",
                        "message": "max_tokens_to_sample must be between 1 and 100000"
                    }
                }
            
            stream = request_data.get('stream', False)
            if stream:
                return {
                    "error": {
                        "type": "invalid_request_error",
                        "message": "Streaming is not supported in Claude Code mode"
                    }
                }
            
            # Format prompt for Claude Code
            if prompt and not prompt.strip().endswith("Assistant:"):
                prompt = f"{prompt}\n\nAssistant:"
            
            # Call Claude Code CLI
            response_text = await self._call_claude_cli_async(prompt, model)
            
            # Build response in legacy format
            response = {
                "completion": response_text,
                "stop_reason": "stop_sequence",
                "model": model
            }
            
            return response
            
        except CLINotFoundError as e:
            return {
                "error": {
                    "type": "not_found_error",
                    "message": str(e),
                }
            }
        except CLITimeoutError as e:
            return {
                "error": {
                    "type": "timeout_error",
                    "message": str(e),
                }
            }
        except CLIError as e:
            logger.error(f"Error handling complete request: {e}", exc_info=True)
            return {
                "error": {
                    "type": "api_error",
                    "message": str(e),
                }
            }
        except Exception as e:
            logger.error(f"Error handling complete request: {e}", exc_info=True)
            return {
                "error": {
                    "type": "api_error",
                    "message": "Failed to process request",
                }
            }
    
    def _format_messages_for_claude(self, messages: List[Dict], system: Optional[str] = None) -> str:
        """
        Format messages into a single prompt for Claude Code CLI.
        """
        prompt_parts = []
        
        # Add system prompt if provided
        if system:
            # Sanitize system prompt
            system_clean = system.replace('\x00', '').strip()
            if system_clean:
                prompt_parts.append(f"System: {system_clean}\n")
        
        # Format conversation history
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            # Handle different content types
            if isinstance(content, list):
                # Handle multipart messages
                text_parts = []
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            text = part.get("text", "")
                            if text:
                                text_parts.append(text)
                        elif part.get("type") == "image":
                            text_parts.append("[Image content not supported in Claude Code mode]")
                    else:
                        text_parts.append(str(part))
                content = " ".join(text_parts)
            elif isinstance(content, dict):
                if content.get("type") == "text":
                    content = content.get("text", "")
                else:
                    content = str(content)
            
            # Sanitize content
            content = str(content).replace('\x00', '').strip()
            
            if role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
            elif role == "system" and content:
                # Handle system messages in the message array
                prompt_parts.append(f"System: {content}")
        
        # Join all parts
        full_prompt = "\n\n".join(prompt_parts)
        
        # Add final Human/Assistant markers if needed
        if full_prompt and not full_prompt.strip().endswith("Assistant:"):
            full_prompt += "\n\nAssistant:"
        
        return full_prompt
    
    async def _call_claude_cli_async(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Call Claude Code CLI asynchronously with security improvements.
        """
        # Build command with proper escaping
        cmd = [self.claude_command, "--print"]
        
        # Map model names to Claude Code equivalents
        if model:
            model_map = {
                "claude-3-opus-20240229": "opus",
                "claude-3-sonnet-20240229": "sonnet",
                "claude-3-haiku-20240307": "haiku",
                "claude-3-5-sonnet-20241022": "sonnet",
                "claude-3-5-haiku-20241022": "haiku",
                "claude-2.1": "claude-2",
                "claude-2.0": "claude-2",
                "claude-instant-1.2": "claude-instant"
            }
            
            # Try to map the model name
            short_name = None
            for full_name, mapped_name in model_map.items():
                if full_name in model:
                    short_name = mapped_name
                    break
            
            if not short_name:
                # If no exact match, try to extract the model type
                model_lower = model.lower()
                for known_type in ["opus", "sonnet", "haiku", "claude-2", "claude-instant"]:
                    if known_type in model_lower:
                        short_name = known_type
                        break
            
            if short_name:
                cmd.extend(["--model", short_name])
        
        logger.debug(f"Running Claude CLI with model: {model}")
        
        try:
            response_text = await run_subprocess_async(
                cmd, prompt, "Claude Code", include_stderr=False
            )
        except CLINotFoundError as e:
            logger.error("Claude Code CLI not found")
            raise e
        except CLITimeoutError as e:
            logger.error("Claude Code CLI timed out")
            raise e
        except CLIError as e:
            logger.error(f"Error calling Claude Code: {e}")
            raise

        # Validate response isn't too large
        if len(response_text) > MAX_PROMPT_LENGTH:
            logger.warning("Claude Code response truncated due to length")
            response_text = response_text[:MAX_PROMPT_LENGTH]

        logger.debug(f"Claude Code response length: {len(response_text)} chars")

        return response_text
