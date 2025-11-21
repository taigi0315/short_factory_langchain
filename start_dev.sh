#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting ShortFactory Development Environment...${NC}"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    make setup-backend
fi

# Check if fastapi is installed in venv
if ! ./venv/bin/python -c "import fastapi" 2>/dev/null; then
    echo -e "${BLUE}📦 Installing backend dependencies...${NC}"
    make setup-backend
fi

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
    make setup-frontend
fi

echo -e "${GREEN}✅ Environment ready!${NC}"

# Function to run backend
run_backend() {
    echo -e "${BLUE}🐍 Starting Backend (Port 8001)...${NC}"
    make run-backend
}

# Function to run frontend
run_frontend() {
    echo -e "${BLUE}⚛️  Starting Frontend (Port 3000)...${NC}"
    make run-frontend
}

# If on macOS, try to open a new tab for frontend
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${BLUE}🖥️  Detected macOS. Opening Frontend in a new terminal tab...${NC}"
    
    # Open new tab/window for frontend
    osascript -e 'tell application "Terminal" to do script "cd \"'"$PWD"'\" && make run-frontend"'
    
    # Run backend in current tab
    run_backend
else
    echo -e "${BLUE}⚠️  Not on macOS. You need to run the frontend manually in another terminal.${NC}"
    echo -e "Run: ${GREEN}make run-frontend${NC}"
    echo ""
    run_backend
fi
