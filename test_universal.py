#!/usr/bin/env python3
"""
Test script to verify the universal proxy works with different scenarios.
"""
import os
import subprocess
import time
import json
from anthropic import Anthropic
import pytest

pytest.skip("integration tests requiring network/proxy", allow_module_level=True)

def test_direct_http_request():
    """Test direct HTTP request through proxy."""
    print("\n1️⃣  Testing Direct HTTP Request (using requests library)")
    print("-" * 50)
    
    # Set proxy environment
    os.environ['HTTP_PROXY'] = 'http://localhost:8080'
    os.environ['HTTPS_PROXY'] = 'http://localhost:8080'
    
    headers = {
        'x-api-key': '999999999999',
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
    }
    
    data = {
        'model': 'claude-3-sonnet-20240229',
        'max_tokens': 50,
        'messages': [
            {'role': 'user', 'content': 'Reply with "Hello from Claude Code via proxy!"'}
        ]
    }
    
    try:
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=data,
            verify=False,  # Skip SSL verification for testing
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Response: {result['content'][0]['text']}")
            if 'msg_claude_code' in result.get('id', ''):
                print("✅ Confirmed: Routed through Claude Code")
            return True
        else:
            print(f"❌ Failed with status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_anthropic_sdk():
    """Test using the official Anthropic SDK through proxy."""
    print("\n2️⃣  Testing Anthropic SDK (through proxy)")
    print("-" * 50)
    
    # Set proxy environment
    os.environ['HTTP_PROXY'] = 'http://localhost:8080'
    os.environ['HTTPS_PROXY'] = 'http://localhost:8080'
    
    try:
        client = Anthropic(api_key='999999999999')
        
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=50,
            messages=[
                {"role": "user", "content": "Say 'SDK works through proxy!'"}
            ]
        )
        
        print(f"✅ Success! Response: {message.content[0].text}")
        print(f"   Message ID: {message.id}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_curl_command():
    """Test using curl through proxy."""
    print("\n3️⃣  Testing cURL Command (through proxy)")
    print("-" * 50)
    
    curl_cmd = [
        'curl', '-x', 'http://localhost:8080',
        'https://api.anthropic.com/v1/messages',
        '-H', 'x-api-key: 999999999999',
        '-H', 'anthropic-version: 2023-06-01',
        '-H', 'content-type: application/json',
        '-d', json.dumps({
            'model': 'claude-3-sonnet-20240229',
            'max_tokens': 50,
            'messages': [{'role': 'user', 'content': 'Say "cURL works!"'}]
        }),
        '-k',  # Skip SSL verification
        '--silent'
    ]
    
    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            response = json.loads(result.stdout)
            if 'content' in response:
                print(f"✅ Success! Response: {response['content'][0]['text']}")
                return True
            else:
                print(f"❌ Unexpected response: {response}")
                return False
        else:
            print(f"❌ cURL failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_nodejs_script():
    """Test Node.js script through proxy."""
    print("\n4️⃣  Testing Node.js Script (through proxy)")
    print("-" * 50)
    
    # Create a simple Node.js test script
    nodejs_script = """
const https = require('https');

process.env.HTTP_PROXY = 'http://localhost:8080';
process.env.HTTPS_PROXY = 'http://localhost:8080';
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'; // Skip SSL verification for testing

const data = JSON.stringify({
  model: 'claude-3-sonnet-20240229',
  max_tokens: 50,
  messages: [{role: 'user', content: 'Say "Node.js works!"'}]
});

const options = {
  hostname: 'api.anthropic.com',
  port: 443,
  path: '/v1/messages',
  method: 'POST',
  headers: {
    'x-api-key': '999999999999',
    'anthropic-version': '2023-06-01',
    'Content-Type': 'application/json',
    'Content-Length': data.length
  }
};

const req = https.request(options, (res) => {
  let body = '';
  res.on('data', (chunk) => body += chunk);
  res.on('end', () => {
    const response = JSON.parse(body);
    if (response.content) {
      console.log('Success:', response.content[0].text);
    } else {
      console.log('Error:', body);
    }
  });
});

req.on('error', (e) => console.error('Error:', e));
req.write(data);
req.end();
"""
    
    # Write the script
    with open('test_node.js', 'w') as f:
        f.write(nodejs_script)
    
    try:
        # Check if node is installed
        subprocess.run(['node', '--version'], capture_output=True, check=True)
        
        # Run the Node.js script
        result = subprocess.run(
            ['node', 'test_node.js'],
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, 
                 'HTTP_PROXY': 'http://localhost:8080',
                 'HTTPS_PROXY': 'http://localhost:8080'}
        )
        
        if 'Success:' in result.stdout:
            response = result.stdout.split('Success:')[1].strip()
            print(f"✅ Success! Response: {response}")
            return True
        else:
            print(f"❌ Failed: {result.stdout} {result.stderr}")
            return False
            
    except subprocess.CalledProcessError:
        print("⚠️  Node.js not installed - skipping test")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists('test_node.js'):
            os.remove('test_node.js')


def main():
    """Run all tests."""
    print("\n🧪 UNIVERSAL PROXY TESTS 🧪")
    print("=" * 50)
    print("Testing proxy with various tools and languages...")
    print("\n⚠️  Make sure the proxy is running on localhost:8080")
    print("   Run: ./start_proxy.sh or python proxy_server.py")
    
    input("\nPress Enter to start tests...")
    
    # Run tests
    results = []
    
    results.append(("Direct HTTP Request", test_direct_http_request()))
    results.append(("Anthropic SDK", test_anthropic_sdk()))
    results.append(("cURL Command", test_curl_command()))
    
    node_result = test_nodejs_script()
    if node_result is not None:
        results.append(("Node.js Script", node_result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    for test_name, result in results:
        if result is True:
            print(f"✅ {test_name}: PASSED")
        elif result is False:
            print(f"❌ {test_name}: FAILED")
        else:
            print(f"⚠️  {test_name}: SKIPPED")
    
    passed = sum(1 for _, r in results if r is True)
    total = len([r for _, r in results if r is not None])
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The proxy works universally!")
    else:
        print("\n⚠️  Some tests failed. Check the proxy configuration.")


if __name__ == "__main__":
    main()