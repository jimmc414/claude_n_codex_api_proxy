"""
Claude Code Client - Interface for routing API calls to Claude Code CLI
"""
import json
import subprocess
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from anthropic.types import Message, TextBlock, Usage


class ClaudeCodeClient:
    """
    Client that interfaces with Claude Code CLI for local inference.
    Converts Anthropic API format to Claude Code CLI format and back.
    """
    
    def __init__(self):
        self.claude_command = "claude"
    
    def _format_messages_for_claude(self, messages: List[Dict], system: Optional[str] = None) -> str:
        """
        Format messages into a single prompt for Claude Code CLI.
        """
        prompt_parts = []
        
        # Add system prompt if provided
        if system:
            prompt_parts.append(f"System: {system}\n")
        
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
                            text_parts.append(part.get("text", ""))
                    else:
                        text_parts.append(str(part))
                content = " ".join(text_parts)
            
            if role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        # Join all parts
        full_prompt = "\n\n".join(prompt_parts)
        
        # Add final Human/Assistant markers if needed
        if not full_prompt.strip().endswith("Assistant:"):
            full_prompt += "\n\nAssistant:"
        
        return full_prompt
    
    def _call_claude_cli(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Call Claude Code CLI with the formatted prompt.
        """
        cmd = [self.claude_command, "--print"]
        
        # Add model selection if specified and supported
        if model:
            # Map common model names to Claude Code equivalents
            model_map = {
                "claude-3-opus-20240229": "opus",
                "claude-3-sonnet-20240229": "sonnet",
                "claude-3-haiku-20240307": "haiku",
                "claude-3-5-sonnet-20241022": "sonnet",
                "claude-3-5-haiku-20241022": "haiku"
            }
            
            # Extract model name if it's a full model ID
            for full_name, short_name in model_map.items():
                if full_name in model:
                    cmd.extend(["--model", short_name])
                    break
            else:
                # Try using the model name directly if not in map
                if any(name in model.lower() for name in ["opus", "sonnet", "haiku"]):
                    model_short = next((name for name in ["opus", "sonnet", "haiku"] if name in model.lower()), "sonnet")
                    cmd.extend(["--model", model_short])
        
        try:
            # Run Claude Code CLI, passing the prompt via stdin to avoid
            # command-line length limits
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error calling Claude Code"
                raise Exception(f"Claude Code CLI error: {error_msg}")
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise Exception("Claude Code CLI timed out after 120 seconds")
        except FileNotFoundError:
            raise Exception("Claude Code CLI not found. Please ensure 'claude' is installed and in PATH")
        except Exception as e:
            raise Exception(f"Error calling Claude Code: {str(e)}")
    
    def create_message(
        self,
        messages: List[Dict],
        model: str,
        max_tokens: int,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        stream: bool = False
    ) -> Message:
        """
        Create a message using Claude Code CLI.
        Returns an Anthropic Message object for compatibility.
        """
        if stream:
            raise NotImplementedError("Streaming is not yet supported with Claude Code routing")
        
        # Format the prompt for Claude Code
        prompt = self._format_messages_for_claude(messages, system)
        
        # Call Claude Code CLI
        response_text = self._call_claude_cli(prompt, model)
        
        # Create a Message object that matches Anthropic's format
        message = Message(
            id="msg_claude_code_" + datetime.now().strftime("%Y%m%d%H%M%S"),
            content=[TextBlock(text=response_text, type="text")],
            model=model,
            role="assistant",
            stop_reason="end_turn",
            stop_sequence=None,
            type="message",
            usage=Usage(
                input_tokens=len(prompt.split()),  # Rough estimate
                output_tokens=len(response_text.split()),  # Rough estimate
                cache_creation_input_tokens=None,
                cache_read_input_tokens=None
            )
        )
        
        return message
    
    async def acreate_message(
        self,
        messages: List[Dict],
        model: str,
        max_tokens: int,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        stream: bool = False
    ) -> Message:
        """
        Async version of create_message.
        """
        if stream:
            raise NotImplementedError("Streaming is not yet supported with Claude Code routing")
        
        # Format the prompt for Claude Code
        prompt = self._format_messages_for_claude(messages, system)
        
        # Call Claude Code CLI asynchronously
        cmd = [self.claude_command, "--print"]
        
        # Add model selection if specified
        if model:
            model_map = {
                "claude-3-opus-20240229": "opus",
                "claude-3-sonnet-20240229": "sonnet",
                "claude-3-haiku-20240307": "haiku",
                "claude-3-5-sonnet-20241022": "sonnet",
                "claude-3-5-haiku-20241022": "haiku"
            }
            
            for full_name, short_name in model_map.items():
                if full_name in model:
                    cmd.extend(["--model", short_name])
                    break
            else:
                if any(name in model.lower() for name in ["opus", "sonnet", "haiku"]):
                    model_short = next((name for name in ["opus", "sonnet", "haiku"] if name in model.lower()), "sonnet")
                    cmd.extend(["--model", model_short])
        
        try:
            # Run Claude Code CLI asynchronously, sending the prompt via stdin
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
                error_msg = stderr.decode() if stderr else "Unknown error calling Claude Code"
                raise Exception(f"Claude Code CLI error: {error_msg}")
            
            response_text = stdout.decode().strip()
            
        except asyncio.TimeoutError:
            raise Exception("Claude Code CLI timed out after 120 seconds")
        except FileNotFoundError:
            raise Exception("Claude Code CLI not found. Please ensure 'claude' is installed and in PATH")
        except Exception as e:
            raise Exception(f"Error calling Claude Code: {str(e)}")
        
        # Create a Message object that matches Anthropic's format
        message = Message(
            id="msg_claude_code_" + datetime.now().strftime("%Y%m%d%H%M%S"),
            content=[TextBlock(text=response_text, type="text")],
            model=model,
            role="assistant",
            stop_reason="end_turn",
            stop_sequence=None,
            type="message",
            usage=Usage(
                input_tokens=len(prompt.split()),
                output_tokens=len(response_text.split()),
                cache_creation_input_tokens=None,
                cache_read_input_tokens=None
            )
        )
        
        return message