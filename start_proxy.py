#!/usr/bin/env python3
"""Cross-platform launcher for Anthropic API proxy server."""
import argparse
import shutil
import subprocess
import sys


def command_exists(cmd: str) -> bool:
    """Check if a command exists on PATH."""
    return shutil.which(cmd) is not None


def ensure_dependencies() -> None:
    """Verify required dependencies are available, installing if needed."""
    if not command_exists("claude"):
        print("⚠️  Warning: Claude Code CLI not found; local routing will fail.")

    try:
        import mitmproxy  # noqa: F401
    except Exception:
        print("Installing Python dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])



def main() -> None:
    parser = argparse.ArgumentParser(description="Anthropic API Proxy Server Launcher")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default="8080")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--allowed-paths", help="Comma-separated regex patterns to replace default allowed paths")
    parser.add_argument("--allowed-path", action="append", default=[],
                        help="Additional regex pattern to allow")
    args = parser.parse_args()

    ensure_dependencies()

    cmd = [sys.executable, "proxy_server.py", "--host", args.host, "--port", args.port]
    if args.verbose:
        cmd.append("--verbose")
    if args.allowed_paths:
        cmd.extend(["--allowed-paths", args.allowed_paths])
    for pattern in args.allowed_path:
        cmd.extend(["--allowed-path", pattern])
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as exc:
        print(f"Proxy server exited with status {exc.returncode}", file=sys.stderr)
        sys.exit(exc.returncode)


if __name__ == "__main__":
    main()
