#!/usr/bin/env python3
"""
Example usage of the Anthropic Router that demonstrates both normal API calls
and Claude Code routing when the API key is all 9s.
"""
import asyncio
from anthropic_router import AnthropicRouter, AsyncAnthropicRouter, create_client
import os


def example_basic_usage():
    """Basic example showing how to use the router."""
    print("=" * 60)
    print("BASIC USAGE EXAMPLE")
    print("=" * 60)
    
    # Example 1: Normal Anthropic API usage
    print("\n1. Normal Anthropic API call (requires valid API key):")
    print("-" * 40)
    
    try:
        # Use a real API key for actual Anthropic API
        client = create_client(api_key="sk-ant-api03-your-real-key-here")
        
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Say hello in one sentence."}
            ]
        )
        
        print(f"Response: {message.content[0].text}")
        print(f"Model: {message.model}")
        print(f"Usage: {message.usage.input_tokens} in, {message.usage.output_tokens} out")
        
    except Exception as e:
        print(f"Note: This would work with a valid API key. Error: {e}")
    
    # Example 2: Claude Code routing with all 9s
    print("\n2. Claude Code routing (API key = all 9s):")
    print("-" * 40)
    
    try:
        # Use all 9s to trigger Claude Code routing
        client = create_client(api_key="999999999999")
        
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "What is 2+2?"}
            ]
        )
        
        print(f"Response: {message.content[0].text}")
        print(f"Model: {message.model}")
        print(f"Routed to: Claude Code (local inference)")
        
    except Exception as e:
        print(f"Error: {e}")


def example_with_system_prompt():
    """Example with system prompt."""
    print("\n" + "=" * 60)
    print("SYSTEM PROMPT EXAMPLE")
    print("=" * 60)
    
    # Use Claude Code routing
    client = create_client(api_key="999999999999")
    
    try:
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=200,
            system="You are a helpful assistant that speaks like a pirate.",
            messages=[
                {"role": "user", "content": "Tell me about Python programming."}
            ]
        )
        
        print(f"Response: {message.content[0].text}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_conversation():
    """Example with multi-turn conversation."""
    print("\n" + "=" * 60)
    print("CONVERSATION EXAMPLE")
    print("=" * 60)
    
    # Use Claude Code routing
    client = create_client(api_key="999999999999")
    
    conversation = [
        {"role": "user", "content": "What's the capital of France?"},
        {"role": "assistant", "content": "The capital of France is Paris."},
        {"role": "user", "content": "What's its population?"}
    ]
    
    try:
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=200,
            messages=conversation
        )
        
        print("Conversation:")
        for msg in conversation:
            role = "Human" if msg["role"] == "user" else "Assistant"
            print(f"  {role}: {msg['content']}")
        print(f"  Assistant: {message.content[0].text}")
        
    except Exception as e:
        print(f"Error: {e}")


async def example_async_usage():
    """Example of async usage."""
    print("\n" + "=" * 60)
    print("ASYNC USAGE EXAMPLE")
    print("=" * 60)
    
    # Use Claude Code routing with async client
    client = AsyncAnthropicRouter(api_key="999999999999")
    
    try:
        message = await client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "What is the meaning of life?"}
            ]
        )
        
        print(f"Async Response: {message.content[0].text}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_environment_variable():
    """Example using environment variable for API key."""
    print("\n" + "=" * 60)
    print("ENVIRONMENT VARIABLE EXAMPLE")
    print("=" * 60)
    
    # Set environment variable to all 9s
    os.environ["ANTHROPIC_API_KEY"] = "999999999999"
    
    # Create client without explicit API key
    client = create_client()
    
    try:
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Hello, how are you?"}
            ]
        )
        
        print(f"Response: {message.content[0].text}")
        print("API key source: Environment variable (ANTHROPIC_API_KEY)")
        print("Routing: Claude Code (detected all 9s)")
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all examples."""
    print("\n" + "🚀 ANTHROPIC ROUTER EXAMPLES 🚀")
    print("=" * 60)
    print("This demonstrates routing API calls to Claude Code")
    print("when the API key is set to all 9s.")
    print("=" * 60)
    
    # Run synchronous examples
    example_basic_usage()
    example_with_system_prompt()
    example_conversation()
    example_environment_variable()
    
    # Run async example
    print("\nRunning async example...")
    asyncio.run(example_async_usage())
    
    print("\n" + "=" * 60)
    print("EXAMPLES COMPLETE")
    print("=" * 60)
    print("\nTo use in your own code:")
    print("1. Set API key to all 9s to use Claude Code")
    print("2. Use a real API key to use Anthropic API")
    print("3. Import: from anthropic_router import create_client")
    print("4. Use like normal Anthropic client!")


if __name__ == "__main__":
    main()
