"Gemini Proxy Handler - Handles API requests routed through the proxy."
import json
import asyncio
from typing import Any, Dict, List, Optional
import uuid
import logging

logger = logging.getLogger(__name__)

# Security constants
MAX_PROMPT_LENGTH = 100000
MAX_MESSAGE_COUNT = 100
MAX_MESSAGE_LENGTH = 50000
VALID_MODELS = {
    "gemini-pro",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.0-pro",
    "gemini-ultra"
}

class GeminiProxyHandler:
    """
    Handles Google Generative AI API requests that need to be routed to Gemini CLI.
    Converts HTTP API requests to Gemini CLI calls and back.
    """
    
    def __init__(self):
        self.gemini_command = "gemini"
    
    def _validate_contents(self, contents: List[Dict]) -> Optional[str]:
        """Validate contents array for security and correctness."""
        if not isinstance(contents, list):
            # The API also accepts a single object sometimes, but usually list
            return "Contents must be a list"
            
        if len(contents) > MAX_MESSAGE_COUNT:
            return f"Too many content items (max {MAX_MESSAGE_COUNT})"
            
        for i, content in enumerate(contents):
            if not isinstance(content, dict):
                return f"Content item {i} must be an object"
                
            parts = content.get("parts")
            if not parts:
                return f"Content item {i} missing parts"
            
            # Check size
            if len(str(parts)) > MAX_MESSAGE_LENGTH:
                return f"Content item {i} too large"
                
        return None

    def _format_contents_for_gemini(self, contents: List[Dict]) -> str:
        """Format JSON contents into a text prompt for the CLI."""
        prompt_parts = []
        for content in contents:
            role = content.get("role", "user")
            parts = content.get("parts", [])
            
            text_content = ""
            if isinstance(parts, list):
                for part in parts:
                    if isinstance(part, dict):
                        text_content += part.get("text", "")
                    else:
                        text_content += str(part)
            
            if role == "user":
                prompt_parts.append(f"User: {text_content}")
            elif role == "model":
                prompt_parts.append(f"Model: {text_content}")
            else:
                prompt_parts.append(f"{role}: {text_content}")
                
        return "\n\n".join(prompt_parts)

    async def handle_generate_content_request(self, request_data: Dict[str, Any], method: str, path: str) -> Dict[str, Any]:
        """
        Handle generateContent endpoint requests.
        """
        if method != 'POST':
            return {
                "error": {
                    "code": 405,
                    "message": f"Method {method} not allowed",
                    "status": "METHOD_NOT_ALLOWED"
                }
            }
            
        try:
            # Extract model from path (e.g., /v1beta/models/gemini-pro:generateContent)
            # Simple extraction
            model = "gemini-pro" # default
            if "models/" in path:
                parts = path.split("models/")[1].split(":")
                if parts:
                    model = parts[0]
            
            # Validate request
            contents = request_data.get("contents", [])
            error = self._validate_contents(contents)
            if error:
                return {
                    "error": {
                        "code": 400,
                        "message": error,
                        "status": "INVALID_ARGUMENT"
                    }
                }
            
            # Check params
            generation_config = request_data.get("generationConfig", {})
            if generation_config.get("maxOutputTokens", 0) > 100000:
                 return {
                    "error": {
                        "code": 400,
                        "message": "maxOutputTokens too large",
                        "status": "INVALID_ARGUMENT"
                    }
                }

            # Format prompt
            prompt = self._format_contents_for_gemini(contents)
            
            if len(prompt) > MAX_PROMPT_LENGTH:
                return {
                    "error": {
                        "code": 400,
                        "message": "Prompt too long",
                        "status": "INVALID_ARGUMENT"
                    }
                }
                
            # Call CLI
            response_text = await self._call_gemini_cli_async(prompt, model)
            
            # Construct Gemini API response
            response = {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": response_text
                                }
                            ],
                            "role": "model"
                        },
                        "finishReason": "STOP",
                        "index": 0,
                        "safetyRatings": [] # Omitting for local CLI
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": len(prompt.split()),
                    "candidatesTokenCount": len(response_text.split()),
                    "totalTokenCount": len(prompt.split()) + len(response_text.split())
                }
            }
            
            return response

        except asyncio.TimeoutError:
             return {
                "error": {
                    "code": 504,
                    "message": "Request timed out",
                    "status": "DEADLINE_EXCEEDED"
                }
            }
        except Exception as e:
            logger.error(f"Error handling Gemini request: {e}", exc_info=True)
            return {
                "error": {
                    "code": 500,
                    "message": "Internal proxy error",
                    "status": "INTERNAL"
                }
            }

    async def _call_gemini_cli_async(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Call Gemini CLI asynchronously.
        """
        cmd = [self.gemini_command]
        
        if model:
            # Ensure we just get the model name
            model_name = model.split('/')[-1]
            cmd.extend(["--model", model_name])
            
        logger.debug(f"Running Gemini CLI with model: {model}")
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=prompt.encode('utf-8')),
                timeout=120
            )
            
            if proc.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Unknown error"
                logger.error(f"Gemini CLI returned non-zero: {proc.returncode}")
                raise Exception("Gemini CLI error")
            
            response_text = stdout.decode('utf-8', errors='ignore').strip()
            
            if len(response_text) > MAX_PROMPT_LENGTH:
                 response_text = response_text[:MAX_PROMPT_LENGTH]
                 
            return response_text
            
        except asyncio.TimeoutError:
            logger.error("Gemini CLI timed out")
            raise Exception("Gemini CLI timed out")
        except FileNotFoundError:
            logger.error("Gemini CLI not found")
            raise Exception("Gemini CLI not found")
        except Exception as e:
            logger.error(f"Error calling Gemini: {type(e).__name__}")
            raise
