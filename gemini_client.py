"Gemini Client - Interface for routing API calls to Gemini CLI"
import subprocess
import asyncio
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass

@dataclass
class GenerationConfig:
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    candidate_count: Optional[int] = None
    max_output_tokens: Optional[int] = None
    stop_sequences: Optional[List[str]] = None

class GeminiClient:
    """
    Client that interfaces with Gemini CLI for local inference.
    Converts Google Generative AI API format to Gemini CLI format and back.
    """
    
    def __init__(self):
        self.gemini_command = "gemini"
    
    def _format_contents_for_gemini(self, contents: Union[str, List[Dict], Dict]) -> str:
        """
        Format contents into a single prompt for Gemini CLI.
        """
        if isinstance(contents, str):
            return contents
            
        prompt_parts = []
        
        # Handle single dict (one message) or list of messages
        if isinstance(contents, dict):
            contents = [contents]
            
        for msg in contents:
            role = msg.get("role", "user")
            parts = msg.get("parts", [])
            
            content_text = ""
            if isinstance(parts, list):
                for part in parts:
                    if isinstance(part, dict):
                        content_text += part.get("text", "")
                    elif isinstance(part, str):
                        content_text += part
            elif isinstance(parts, str):
                content_text = parts
            
            if role == "user":
                prompt_parts.append(f"User: {content_text}")
            elif role == "model":
                prompt_parts.append(f"Model: {content_text}")
            else:
                prompt_parts.append(f"{role}: {content_text}")
        
        return "\n\n".join(prompt_parts)
    
    def _call_gemini_cli(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Call Gemini CLI with the formatted prompt.
        """
        cmd = [self.gemini_command]
        
        # Add model selection if specified
        if model:
            # Strip 'models/' prefix if present
            model_name = model.split('/')[-1] if '/' in model else model
            cmd.extend(["--model", model_name])
        
        try:
            # Run Gemini CLI, passing the prompt via stdin
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error calling Gemini CLI"
                raise Exception(f"Gemini CLI error: {error_msg}")
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise Exception("Gemini CLI timed out after 120 seconds")
        except FileNotFoundError:
            raise Exception("Gemini CLI not found. Please ensure 'gemini' is installed and in PATH")
        except Exception as e:
            raise Exception(f"Error calling Gemini: {str(e)}")
            
    async def _call_gemini_cli_async(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Call Gemini CLI asynchronously.
        """
        cmd = [self.gemini_command]
        
        if model:
            model_name = model.split('/')[-1] if '/' in model else model
            cmd.extend(["--model", model_name])
            
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=prompt.encode()),
                timeout=120
            )
            
            if proc.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error calling Gemini CLI"
                raise Exception(f"Gemini CLI error: {error_msg}")
            
            return stdout.decode().strip()
            
        except asyncio.TimeoutError:
            raise Exception("Gemini CLI timed out after 120 seconds")
        except FileNotFoundError:
            raise Exception("Gemini CLI not found. Please ensure 'gemini' is installed and in PATH")
        except Exception as e:
            raise Exception(f"Error calling Gemini: {str(e)}")

    def generate_content(
        self, 
        model: str, 
        contents: Union[str, List[Dict]], 
        generation_config: Optional[GenerationConfig] = None,
        stream: bool = False
    ) -> Any:
        """
        Generate content using Gemini CLI.
        Returns a simpler object that mimics google.generativeai.types.GenerateContentResponse
        """
        if stream:
            raise NotImplementedError("Streaming is not yet supported with Gemini CLI routing")
            
        prompt = self._format_contents_for_gemini(contents)
        response_text = self._call_gemini_cli(prompt, model)
        
        return self._create_response_object(response_text)

    async def generate_content_async(
        self, 
        model: str, 
        contents: Union[str, List[Dict]], 
        generation_config: Optional[GenerationConfig] = None,
        stream: bool = False
    ) -> Any:
        """Async version of generate_content."""
        if stream:
            raise NotImplementedError("Streaming is not yet supported with Gemini CLI routing")
            
        prompt = self._format_contents_for_gemini(contents)
        response_text = await self._call_gemini_cli_async(prompt, model)
        
        return self._create_response_object(response_text)

    def _create_response_object(self, text: str) -> Any:
        """Creates a response object mimicking the SDK's response."""
        # Simple dummy class to mimic the structure
        class Candidate:
            def __init__(self, text):
                self.content = type('Content', (), {'parts': [type('Part', (), {'text': text})()]})()
                self.finish_reason = 1 # STOP

        class Response:
            def __init__(self, text):
                self.text = text
                self.candidates = [Candidate(text)]
                self.parts = [type('Part', (), {'text': text})()]
                
        return Response(text)
