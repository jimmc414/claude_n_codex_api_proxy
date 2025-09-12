#!/usr/bin/env python3
"""
Simple test script to verify the Claude Code routing functionality.
"""
import os
from anthropic_router import create_client


def test_claude_code_routing():
    """Test that API key with all 9s routes to Claude Code."""
    print("Testing Claude Code routing...")
    print("-" * 40)
    
    # Create client with all 9s API key
    client = create_client(api_key="999999999999")
    
    try:
        # Make a simple API call
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=50,
            messages=[
                {"role": "user", "content": "Say 'Hello from Claude Code!' if you're working."}
            ]
        )
        
        response_text = message.content[0].text
        print(f"✅ Success! Response: {response_text}")
        print(f"   Message ID: {message.id}")
        print(f"   Model: {message.model}")
        
        # Check that it's using Claude Code (ID should start with msg_claude_code_)
        if message.id.startswith("msg_claude_code_"):
            print("✅ Confirmed: Using Claude Code routing")
        else:
            print("⚠️  Warning: May not be using Claude Code routing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_api_key_detection():
    """Test API key detection logic."""
    print("\nTesting API key detection...")
    print("-" * 40)
    
    test_cases = [
        ("999999999999", True, "All 9s"),
        ("sk-ant-999999999999", True, "With prefix, all 9s"),
        ("123456789012", False, "Random numbers"),
        ("sk-ant-api03-real-key", False, "Real-looking key"),
        ("99999999999", True, "All 9s (11 digits)"),
        ("9999999999999", True, "All 9s (13 digits)"),
    ]
    
    for api_key, should_route, description in test_cases:
        client = create_client(api_key=api_key)
        is_routing = client._is_claude_code_mode
        
        if is_routing == should_route:
            print(f"✅ {description}: Correctly {'routes' if should_route else 'does not route'} to Claude Code")
        else:
            print(f"❌ {description}: Expected {'routing' if should_route else 'no routing'}, got {'routing' if is_routing else 'no routing'}")


def main():
    print("\n🧪 CLAUDE CODE ROUTER TESTS 🧪")
    print("=" * 40)
    
    # Run tests
    test_api_key_detection()
    print()
    test_claude_code_routing()
    
    print("\n" + "=" * 40)
    print("Tests complete!")


if __name__ == "__main__":
    main()