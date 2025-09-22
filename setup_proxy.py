#!/usr/bin/env python3
"""
Setup script for configuring the Anthropic API proxy.
Generates certificates and provides configuration instructions.
"""
import os
import sys
import subprocess
import time
import platform
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    missing = []
    
    # Check for Claude CLI
    try:
        subprocess.run(['claude', '--version'], capture_output=True, check=True)
        print("  ✅ Claude Code CLI found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ❌ Claude Code CLI not found")
        missing.append("claude")
    
    # Check for Python packages
    try:
        import mitmproxy
        print("  ✅ mitmproxy installed")
    except ImportError:
        print("  ❌ mitmproxy not installed")
        missing.append("mitmproxy")
    
    try:
        import anthropic
        print("  ✅ anthropic package installed")
    except ImportError:
        print("  ❌ anthropic package not installed")
        missing.append("anthropic")
    
    return missing


def install_dependencies():
    """Install missing dependencies."""
    print("\n📦 Installing dependencies...")
    
    # Install Python packages
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
    print("  ✅ Python packages installed")
    
    # Check if Claude CLI needs installation
    try:
        subprocess.run(['claude', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n⚠️  Claude Code CLI not found!")
        print("Please install it manually:")
        print("  npm install -g @anthropic-ai/claude-code")
        print("Or follow instructions at: https://github.com/anthropics/claude-code")


def generate_certificates():
    """Generate SSL certificates for HTTPS interception."""
    cert_dir = Path.home() / '.mitmproxy'
    cert_dir.mkdir(exist_ok=True)
    
    print("\n🔐 Setting up SSL certificates...")
    
    # Check if mitmproxy CA certificate already exists
    ca_cert = cert_dir / 'mitmproxy-ca-cert.pem'
    if ca_cert.exists():
        print(f"  ✅ CA certificate already exists at {ca_cert}")
    else:
        print("  📝 Generating new CA certificate...")
        # Run mitmproxy once to generate certificates
        try:
            proc = subprocess.Popen(
                ['mitmdump', '--quiet'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except Exception as e:
            print(f"  ⚠️  Could not auto-generate certificate: {e}")
            print("  Run 'mitmdump' once manually to generate certificates")
        else:
            try:
                deadline = time.monotonic() + 10
                success = False

                while time.monotonic() < deadline:
                    if ca_cert.exists():
                        success = True
                        break

                    if proc.poll() is not None:
                        break

                    time.sleep(0.1)

                proc_returncode = proc.poll()

                if success or ca_cert.exists():
                    print(f"  ✅ CA certificate generated at {ca_cert}")
                else:
                    reason = "timed out waiting for mitmdump to create CA certificate"
                    if proc_returncode is not None:
                        reason = (
                            "mitmdump exited "
                            f"with code {proc_returncode} before creating CA certificate"
                        )
                    print(f"  ⚠️  Could not auto-generate certificate: {reason}")
                    print("  Run 'mitmdump' once manually to generate certificates")
            finally:
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=5)

    return cert_dir


def print_configuration_instructions():
    """Print instructions for configuring different tools and platforms."""
    system = platform.system()
    
    print("\n" + "=" * 60)
    print("📋 CONFIGURATION INSTRUCTIONS")
    print("=" * 60)
    
    print("\n1️⃣  ENVIRONMENT VARIABLES (Universal Method):")
    print("-" * 40)
    print("Add these to your shell config or set before running commands:")
    print()
    print("  export HTTP_PROXY=http://localhost:8080")
    print("  export HTTPS_PROXY=http://localhost:8080")
    print("  export ANTHROPIC_API_KEY=999999999999  # All 9s for Claude Code")
    print()
    
    print("\n2️⃣  LANGUAGE-SPECIFIC CONFIGURATION:")
    print("-" * 40)
    
    print("\n🐍 Python:")
    print("  import os")
    print("  os.environ['HTTP_PROXY'] = 'http://localhost:8080'")
    print("  os.environ['HTTPS_PROXY'] = 'http://localhost:8080'")
    print("  os.environ['ANTHROPIC_API_KEY'] = '999999999999'")
    print()
    
    print("\n📦 Node.js:")
    print("  process.env.HTTP_PROXY = 'http://localhost:8080';")
    print("  process.env.HTTPS_PROXY = 'http://localhost:8080';")
    print("  process.env.ANTHROPIC_API_KEY = '999999999999';")
    print()
    
    print("\n🔧 cURL:")
    print("  curl -x http://localhost:8080 \\")
    print("    https://api.anthropic.com/v1/messages \\")
    print("    -H 'x-api-key: 999999999999' \\")
    print("    -H 'content-type: application/json' \\")
    print("    -d '{...}'")
    print()
    
    print("\n3️⃣  SSL/HTTPS SETUP:")
    print("-" * 40)
    cert_dir = Path.home() / '.mitmproxy'
    
    if system == "Darwin":  # macOS
        print("macOS - Add certificate to Keychain:")
        print(f"  sudo security add-trusted-cert -d -r trustRoot \\")
        print(f"    -k /Library/Keychains/System.keychain \\")
        print(f"    {cert_dir}/mitmproxy-ca-cert.pem")
    elif system == "Linux":
        print("Linux - Add certificate to system:")
        print(f"  sudo cp {cert_dir}/mitmproxy-ca-cert.pem \\")
        print(f"    /usr/local/share/ca-certificates/mitmproxy.crt")
        print(f"  sudo update-ca-certificates")
    elif system == "Windows":
        print("Windows - Import certificate:")
        print(f"  1. Open {cert_dir}\\mitmproxy-ca-cert.pem")
        print(f"  2. Install Certificate → Local Machine")
        print(f"  3. Place in 'Trusted Root Certification Authorities'")
    
    print("\n4️⃣  BROWSER CONFIGURATION:")
    print("-" * 40)
    print("Firefox:")
    print("  Settings → Network Settings → Manual proxy configuration")
    print("  HTTP Proxy: localhost, Port: 8080")
    print("  HTTPS Proxy: localhost, Port: 8080")
    print()
    print("Chrome/Edge:")
    print("  Use system proxy settings (set via environment variables)")
    
    print("\n5️⃣  DISABLE PROXY:")
    print("-" * 40)
    print("To disable the proxy and use Anthropic API directly:")
    print("  unset HTTP_PROXY")
    print("  unset HTTPS_PROXY")
    print("Or use a real Anthropic API key instead of all 9s")


def create_test_script():
    """Create a simple test script to verify the proxy works."""
    test_script = """#!/usr/bin/env python3
\"\"\"Test script to verify proxy configuration.\"\"\"
import os
import requests

# Set proxy and API key
os.environ['HTTP_PROXY'] = 'http://localhost:8080'
os.environ['HTTPS_PROXY'] = 'http://localhost:8080'

# Test with all 9s (routes to Claude Code)
print("Testing with all 9s API key (Claude Code routing)...")
response = requests.post(
    'https://api.anthropic.com/v1/messages',
    headers={
        'x-api-key': '999999999999',
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
    },
    json={
        'model': 'claude-3-sonnet-20240229',
        'max_tokens': 50,
        'messages': [{'role': 'user', 'content': 'Say "Hello from Claude Code!"'}]
    },
    verify=False  # For testing, skip SSL verification
)

if response.status_code == 200:
    print("✅ Success! Response:", response.json()['content'][0]['text'])
else:
    print("❌ Failed:", response.status_code, response.text)
"""
    
    with open('test_proxy.py', 'w') as f:
        f.write(test_script)
    os.chmod('test_proxy.py', 0o755)
    print("\n✅ Created test_proxy.py - run it after starting the proxy")


def main():
    """Main setup process."""
    print("🚀 ANTHROPIC API PROXY SETUP")
    print("=" * 60)
    
    # Check dependencies
    missing = check_dependencies()
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        response = input("Install missing dependencies? (y/n): ")
        if response.lower() == 'y':
            install_dependencies()
        else:
            print("Please install dependencies manually before running the proxy.")
            sys.exit(1)
    
    # Generate certificates
    cert_dir = generate_certificates()
    
    # Print configuration instructions
    print_configuration_instructions()
    
    # Create test script
    create_test_script()
    
    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the proxy: ./start_proxy.sh or python proxy_server.py")
    print("2. Configure your environment (see instructions above)")
    print("3. Test with: python test_proxy.py")
    print("\nAPI keys with all 9s will route to Claude Code")
    print("Other API keys will forward to the real Anthropic API")


if __name__ == '__main__':
    main()