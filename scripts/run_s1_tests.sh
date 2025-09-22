#!/bin/bash

# S1 Test Runner Script
# Runs all S1 tests for both backend and frontend

set -e

echo "🚀 Running S1 Tests for Persona Wizard"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Parse command line arguments
BACKEND_ONLY=false
FRONTEND_ONLY=false
VERBOSE=false
COVERAGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only)
            BACKEND_ONLY=true
            shift
            ;;
        --frontend-only)
            FRONTEND_ONLY=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --backend-only    Run only backend tests"
            echo "  --frontend-only   Run only frontend tests"
            echo "  --verbose         Enable verbose output"
            echo "  --coverage        Generate coverage reports"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set verbose flag for pytest if requested
PYTEST_ARGS=""
if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS="-v"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=app --cov-report=html --cov-report=term"
fi

# Function to run backend tests
run_backend_tests() {
    print_status "Running Backend S1 Tests..."
    echo "--------------------------------"
    
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies if needed
    if [ ! -f "venv/pyvenv.cfg" ] || [ ! -d "venv/lib" ]; then
        print_status "Installing backend dependencies..."
        pip install -r requirements.txt
    fi
    
    # Run specific S1 tests
    print_status "Running S1 Backend Tests..."
    
    # Core S1 tests
    python -m pytest tests/test_image_upload.py $PYTEST_ARGS
    python -m pytest tests/test_text_upload.py $PYTEST_ARGS
    
    # Integration tests
    python -m pytest tests/test_s1_integration.py $PYTEST_ARGS
    
    # API contract tests
    python -m pytest tests/test_s1_api_contracts.py $PYTEST_ARGS
    
    # E2E tests
    python -m pytest tests/test_s1_e2e.py $PYTEST_ARGS
    
    # Health tests (basic functionality)
    python -m pytest tests/test_health.py $PYTEST_ARGS
    
    # Preview tests (if available)
    if [ -f "tests/test_preview.py" ]; then
        python -m pytest tests/test_preview.py $PYTEST_ARGS
    fi
    
    deactivate
    cd ..
    
    print_success "Backend S1 Tests Completed!"
}

# Function to run frontend tests
run_frontend_tests() {
    print_status "Running Frontend S1 Tests..."
    echo "---------------------------------"
    
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_warning "Node modules not found. Installing dependencies..."
        npm install
    fi
    
    # Run frontend tests
    print_status "Running S1 Frontend Tests..."
    
    # Run tests with Jest
    if [ "$COVERAGE" = true ]; then
        npm test -- --coverage --watchAll=false
    else
        npm test -- --watchAll=false
    fi
    
    cd ..
    
    print_success "Frontend S1 Tests Completed!"
}

# Function to run integration tests
run_integration_tests() {
    print_status "Running Integration Tests..."
    echo "-------------------------------"
    
    # Start services if not running
    print_status "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check if backend is ready
    print_status "Checking backend health..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
            print_success "Backend is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Backend failed to start within 30 seconds"
            exit 1
        fi
        sleep 1
    done
    
    # Check if frontend is ready
    print_status "Checking frontend health..."
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            print_success "Frontend is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "Frontend may not be ready, continuing with tests..."
            break
        fi
        sleep 1
    done
    
    # Run integration tests
    cd backend
    source venv/bin/activate
    python -m pytest tests/test_s1_integration.py $PYTEST_ARGS
    deactivate
    cd ..
    
    # Stop services
    print_status "Stopping services..."
    docker-compose down
    
    print_success "Integration Tests Completed!"
}

# Main execution
main() {
    echo ""
    print_status "Starting S1 Test Suite..."
    echo ""
    
    # Run backend tests
    if [ "$FRONTEND_ONLY" = false ]; then
        run_backend_tests
        echo ""
    fi
    
    # Run frontend tests
    if [ "$BACKEND_ONLY" = false ]; then
        run_frontend_tests
        echo ""
    fi
    
    # Run integration tests if both are enabled
    if [ "$BACKEND_ONLY" = false ] && [ "$FRONTEND_ONLY" = false ]; then
        run_integration_tests
        echo ""
    fi
    
    print_success "All S1 Tests Completed Successfully! 🎉"
    echo ""
    
    # Show coverage information if requested
    if [ "$COVERAGE" = true ]; then
        print_status "Coverage reports generated:"
        echo "  - Backend: backend/htmlcov/index.html"
        echo "  - Frontend: frontend/coverage/lcov-report/index.html"
    fi
}

# Run main function
main "$@"
