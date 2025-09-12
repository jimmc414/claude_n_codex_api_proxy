#!/bin/bash
# Start script for Anthropic API Proxy Server

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
HOST="127.0.0.1"
PORT="8080"
VERBOSE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --verbose|-v)
            VERBOSE="--verbose"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --host HOST     Host to bind to (default: 127.0.0.1)"
            echo "  --port PORT     Port to listen on (default: 8080)"
            echo "  --verbose, -v   Enable verbose logging"
            echo "  --help, -h      Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down proxy server...${NC}"
    # Kill any background processes
    jobs -p | xargs -r kill 2>/dev/null
    exit 0
}

# Set up trap for clean exit
trap cleanup INT TERM

# Clear screen for clean start
clear

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       ${GREEN}🚀 Anthropic API Proxy Server Launcher 🚀${BLUE}         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo

# Check dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists claude; then
    echo -e "${RED}⚠️  Warning: Claude Code CLI not found${NC}"
    echo "  The proxy will fail when routing to Claude Code."
    echo "  Install with: npm install -g @anthropic-ai/claude-code"
    echo
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if mitmproxy is installed
if ! python3 -c "import mitmproxy" 2>/dev/null; then
    echo -e "${RED}❌ mitmproxy is not installed${NC}"
    echo "Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install dependencies${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ All dependencies satisfied${NC}"
echo

# Display configuration
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Host: ${GREEN}$HOST${NC}"
echo -e "  Port: ${GREEN}$PORT${NC}"
if [ -n "$VERBOSE" ]; then
    echo -e "  Mode: ${YELLOW}Verbose${NC}"
fi
echo

# Display quick setup instructions
echo -e "${BLUE}Quick Setup:${NC}"
echo -e "  1. Set environment variables:"
echo -e "     ${YELLOW}export HTTP_PROXY=http://$HOST:$PORT${NC}"
echo -e "     ${YELLOW}export HTTPS_PROXY=http://$HOST:$PORT${NC}"
echo -e "     ${YELLOW}export ANTHROPIC_API_KEY=999999999999${NC}  # For Claude Code"
echo
echo -e "  2. Or configure your application to use proxy:"
echo -e "     ${YELLOW}http://$HOST:$PORT${NC}"
echo
echo -e "${GREEN}Starting proxy server...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo

# Start the proxy server
python3 proxy_server.py --host "$HOST" --port "$PORT" $VERBOSE

# This line is reached when the proxy stops
echo -e "${GREEN}Proxy server stopped.${NC}"