#!/bin/bash

# Start local server and run Quick Generate test
# This script starts the server in the background and runs the test

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

LOCAL_URL="http://localhost:8000"
PID_FILE="/tmp/blog_writer_api.pid"

echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}Local Test: Quick Generate Mode (Status Code Fix)${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

# Check if server is already running
if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Server already running (PID: $(cat $PID_FILE))${NC}"
    echo -e "${CYAN}Using existing server...${NC}\n"
else
    # Check for required environment variables
    echo -e "${CYAN}Checking environment variables...${NC}"
    
    if [ -z "$DATAFORSEO_API_KEY" ] || [ -z "$DATAFORSEO_API_SECRET" ]; then
        echo -e "${YELLOW}⚠️  DataForSEO credentials not found in environment${NC}"
        echo -e "${CYAN}Attempting to load from Google Secret Manager...${NC}"
        
        if command -v gcloud &> /dev/null; then
            export DATAFORSEO_API_KEY=$(gcloud secrets versions access latest --secret=DATAFORSEO_API_KEY --project=api-ai-blog-writer 2>/dev/null || echo "")
            export DATAFORSEO_API_SECRET=$(gcloud secrets versions access latest --secret=DATAFORSEO_API_SECRET --project=api-ai-blog-writer 2>/dev/null || echo "")
        fi
        
        if [ -z "$DATAFORSEO_API_KEY" ] || [ -z "$DATAFORSEO_API_SECRET" ]; then
            echo -e "${RED}❌ DataForSEO credentials not found!${NC}"
            echo -e "${YELLOW}Please set DATAFORSEO_API_KEY and DATAFORSEO_API_SECRET${NC}"
            echo -e "${CYAN}Or ensure gcloud is configured and secrets exist${NC}"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✅ DataForSEO credentials found${NC}\n"
    
    # Start server in background
    echo -e "${CYAN}Starting local server...${NC}"
    cd "$(dirname "$0")"
    
    # Set default environment variables if not set
    export PORT=${PORT:-8000}
    export HOST=${HOST:-0.0.0.0}
    export DEBUG=${DEBUG:-true}
    
    # Start server
    python3 main.py > /tmp/blog_writer_api.log 2>&1 &
    SERVER_PID=$!
    echo $SERVER_PID > "$PID_FILE"
    
    echo -e "${GREEN}✅ Server started (PID: $SERVER_PID)${NC}"
    echo -e "${CYAN}Logs: /tmp/blog_writer_api.log${NC}\n"
    
    # Wait for server to start
    echo -e "${CYAN}Waiting for server to start...${NC}"
    for i in {1..30}; do
        if curl -s "${LOCAL_URL}/" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Server is ready!${NC}\n"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ Server failed to start after 30 seconds${NC}"
            echo -e "${YELLOW}Check logs: tail -f /tmp/blog_writer_api.log${NC}"
            kill $SERVER_PID 2>/dev/null || true
            rm -f "$PID_FILE"
            exit 1
        fi
        sleep 1
        echo -n "."
    done
    echo ""
fi

# Run the test
echo -e "${BOLD}${BLUE}Running Quick Generate Test...${NC}\n"
./test_local_quick_generate.sh

# Ask if user wants to keep server running
echo ""
echo -e "${CYAN}Server is still running in the background${NC}"
echo -e "${CYAN}To stop it, run: kill $(cat $PID_FILE) && rm $PID_FILE${NC}"
echo -e "${CYAN}Or view logs: tail -f /tmp/blog_writer_api.log${NC}"

