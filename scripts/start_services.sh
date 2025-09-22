#!/bin/bash

# Start Persona Wizard Services
# This script starts Foundry Local and the backend server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Persona Wizard Services...${NC}"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for a service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=0
    
    echo -e "${YELLOW}⏳ Waiting for $service_name to be ready...${NC}"
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $service_name failed to start after $((max_attempts * 2)) seconds${NC}"
    return 1
}

# Start Foundry Local if not already running
FOUNDRY_PORT=53224
if ! check_port $FOUNDRY_PORT; then
    echo -e "${YELLOW}🔧 Starting Foundry Local...${NC}"
    /opt/homebrew/Cellar/foundrylocal/0.6.87/foundry service start &
    FOUNDRY_PID=$!
    
    # Wait for Foundry Local to be ready
    if wait_for_service "http://127.0.0.1:$FOUNDRY_PORT/openai/status" "Foundry Local"; then
        echo -e "${GREEN}✅ Foundry Local started successfully${NC}"
    else
        echo -e "${RED}❌ Failed to start Foundry Local${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Foundry Local is already running${NC}"
fi

# Start Backend Server
BACKEND_PORT=8000
if ! check_port $BACKEND_PORT; then
    echo -e "${YELLOW}🔧 Starting Backend Server...${NC}"
    cd /Users/wynonawynston/persona-wizard
    source venv/bin/activate
    uvicorn backend.app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT &
    BACKEND_PID=$!
    
    # Wait for Backend to be ready
    if wait_for_service "http://localhost:$BACKEND_PORT/healthz" "Backend Server"; then
        echo -e "${GREEN}✅ Backend Server started successfully${NC}"
    else
        echo -e "${RED}❌ Failed to start Backend Server${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Backend Server is already running${NC}"
fi

echo -e "${GREEN}🎉 All services are running!${NC}"
echo -e "${GREEN}   - Foundry Local: http://127.0.0.1:$FOUNDRY_PORT${NC}"
echo -e "${GREEN}   - Backend API: http://localhost:$BACKEND_PORT${NC}"
echo -e "${GREEN}   - API Docs: http://localhost:$BACKEND_PORT/docs${NC}"

# Keep script running and handle cleanup on exit
trap 'echo -e "${YELLOW}🛑 Shutting down services...${NC}"; kill $FOUNDRY_PID $BACKEND_PID 2>/dev/null || true; exit 0' INT TERM

# Wait for background processes
wait
