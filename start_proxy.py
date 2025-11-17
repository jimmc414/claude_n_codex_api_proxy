#!/usr/bin/env python3
"""Cross-platform launcher for Anthropic API proxy server."""
import argparse
import asyncio
import logging
import shutil
import sys

def command_exists(cmd: str) -> bool:
    """Check if a command exists on PATH."""
    return shutil.which(cmd) is not None


def ensure_dependencies() -> None:
    """Verify required dependencies are available, installing if needed."""
    cli_missing = []
    if not command_exists("claude"):
        print("⚠️  Warning: Claude Code CLI not found; local routing will fail.")
        print("   Install with: npm install -g @anthropics/claude-code")
        cli_missing.append("claude")
    if not command_exists("codex"):
        print("⚠️  Warning: Codex CLI not found; codex routing will fail.")
        print("   See https://github.com/openai/openai-codex for installation")
        cli_missing.append("codex")

    if cli_missing:
        print(f"\n⚠️  Missing CLI tools: {', '.join(cli_missing)}")
        print("   The proxy will start but requests with API key '999...' will fail")
        print("   until these tools are installed.\n")

    try:
        import mitmproxy  # noqa: F401
    except Exception:
        import subprocess

        print("Installing Python dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])



def main() -> None:
    parser = argparse.ArgumentParser(description="Anthropic API Proxy Server Launcher")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--allowed-paths",
        help="Comma-separated regex patterns to replace default allowed paths",
    )
    parser.add_argument(
        "--allowed-path",
        action="append",
        default=[],
        help="Additional regex pattern to allow",
    )
    args = parser.parse_args()

    ensure_dependencies()

    import proxy_server

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    override = args.allowed_paths
    if override:
        patterns = [p.strip() for p in override.split(",") if p.strip()]
    else:
        patterns = list(proxy_server.DEFAULT_ALLOWED_PATH_PATTERNS)
    if args.allowed_path:
        patterns.extend(args.allowed_path)
    allowed_paths_regex = proxy_server.build_allowed_paths_regex(patterns)

    try:
        asyncio.run(
            proxy_server.start_proxy(
                args.host,
                args.port,
                allowed_paths_regex=allowed_paths_regex,
            )
        )
    except KeyboardInterrupt:
        print("\nProxy server stopped.")
        sys.exit(0)
    except Exception as exc:
        print(f"Proxy server error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
