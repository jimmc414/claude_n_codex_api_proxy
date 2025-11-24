"""
Gemini API Router that routes to Gemini CLI when API key is all 9s
"""
import os
from typing import Any, Dict, List, Optional, Union
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from gemini_client import GeminiClient

# Global storage for the configured API key
_configured_api_key: Optional[str] = None

def _is_all_nines(api_key: Optional[str]) -> bool:
    """Check if the API key is all 9s."""
    if not api_key:
        return False
    # Remove prefixes or query params if present (though typically just the key string)
    return all(c == '9' for c in api_key)

def configure(api_key: Optional[str] = None, **kwargs):
    """
    Configure the Gemini API.
    """
    global _configured_api_key
    _configured_api_key = api_key or os.environ.get("GOOGLE_API_KEY")
    
    # Always configure the real library just in case, unless we want to prevent it
    # completely for bad keys. But typically we just mirror.
    # However, if it's all 9s, the real library might reject it if we call configure.
    # So we only call real configure if it's NOT all 9s.
    if not _is_all_nines(_configured_api_key):
        genai.configure(api_key=_configured_api_key, **kwargs)

class GenerativeModel:
    """
    A wrapper around google.generativeai.GenerativeModel that routes to Gemini CLI
    when the configured API key is all 9s.
    """
    
    def __init__(
        self, 
        model_name: str,
        generation_config: Optional[GenerationConfig] = None,
        safety_settings: Optional[Any] = None,
        tools: Optional[Any] = None,
        tool_config: Optional[Any] = None,
        system_instruction: Optional[Any] = None
    ):
        self.model_name = model_name
        self.generation_config = generation_config
        self.safety_settings = safety_settings
        self.tools = tools
        self.tool_config = tool_config
        self.system_instruction = system_instruction
        
        # Determine mode based on globally configured key
        self._is_local_mode = _is_all_nines(_configured_api_key)
        
        if self._is_local_mode:
            self.client = GeminiClient()
            self._real_model = None
        else:
            self.client = None
            self._real_model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                safety_settings=safety_settings,
                tools=tools,
                tool_config=tool_config,
                system_instruction=system_instruction
            )
            
    def generate_content(
        self,
        contents: Union[str, List[Dict[str, Any]]],
        generation_config: Optional[GenerationConfig] = None,
        safety_settings: Optional[Any] = None,
        stream: bool = False,
        **kwargs
    ) -> Any:
        """
        Generate content, routing to local CLI if in local mode.
        """
        if self._is_local_mode:
            # Use local Gemini Client
            # Merge config if provided
            config = generation_config or self.generation_config
            
            if stream:
                raise NotImplementedError("Streaming not supported in local mode")
            
            return self.client.generate_content(
                model=self.model_name,
                contents=contents,
                generation_config=config,
                stream=stream
            )
        else:
            # Delegate to real library
            return self._real_model.generate_content(
                contents,
                generation_config=generation_config,
                safety_settings=safety_settings,
                stream=stream,
                **kwargs
            )

    async def generate_content_async(
        self,
        contents: Union[str, List[Dict[str, Any]]],
        generation_config: Optional[GenerationConfig] = None,
        safety_settings: Optional[Any] = None,
        stream: bool = False,
        **kwargs
    ) -> Any:
        """
        Async version of generate_content.
        """
        if self._is_local_mode:
            config = generation_config or self.generation_config
            if stream:
                raise NotImplementedError("Streaming not supported in local mode")
                
            return await self.client.generate_content_async(
                model=self.model_name,
                contents=contents,
                generation_config=config,
                stream=stream
            )
        else:
            return await self._real_model.generate_content_async(
                contents,
                generation_config=generation_config,
                safety_settings=safety_settings,
                stream=stream,
                **kwargs
            )

# Expose other common functions/classes from genai if needed, 
# but mostly GenerativeModel and configure are the entry points.
