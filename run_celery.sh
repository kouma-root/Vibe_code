#!/bin/bash

# Celery Management Script for FinFlow
# This script provides easy commands to manage Celery workers and beat

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="/home/kouma/Desktop/Personal_Projects/Vibe_code"
VENV_DIR="$PROJECT_DIR/venv"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to check if Redis is running
check_redis() {
    if ! redis-cli ping > /dev/null 2>&1; then
        print_warning "Redis is not running. Starting Redis..."
        if command -v redis-server > /dev/null 2>&1; then
            redis-server --daemonize yes
            sleep 2
            if redis-cli ping > /dev/null 2>&1; then
                print_status "Redis started successfully"
            else
                print_error "Failed to start Redis. Please install Redis or start it manually."
                exit 1
            fi
        else
            print_error "Redis is not installed. Please install Redis first:"
            echo "  sudo apt-get install redis-server"
            exit 1
        fi
    else
        print_status "Redis is running"
    fi
}

# Function to activate virtual environment
activate_venv() {
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
        print_status "Virtual environment activated"
    else
        print_error "Virtual environment not found at $VENV_DIR"
        exit 1
    fi
}

# Function to start Celery worker
start_worker() {
    print_header "Starting Celery Worker"
    check_redis
    activate_venv
    cd "$PROJECT_DIR"
    
    print_status "Starting Celery worker..."
    celery -A finflow worker --loglevel=info --concurrency=4
}

# Function to start Celery beat
start_beat() {
    print_header "Starting Celery Beat"
    check_redis
    activate_venv
    cd "$PROJECT_DIR"
    
    print_status "Starting Celery beat scheduler..."
    celery -A finflow beat --loglevel=info
}

# Function to start both worker and beat
start_both() {
    print_header "Starting Celery Worker and Beat"
    check_redis
    activate_venv
    cd "$PROJECT_DIR"
    
    print_status "Starting Celery worker with beat scheduler..."
    celery -A finflow worker --beat --loglevel=info --concurrency=4
}

# Function to start Celery Flower
start_flower() {
    print_header "Starting Celery Flower"
    check_redis
    activate_venv
    cd "$PROJECT_DIR"
    
    # Install flower if not already installed
    if ! python -c "import flower" 2>/dev/null; then
        print_status "Installing Celery Flower..."
        pip install flower
    fi
    
    print_status "Starting Celery Flower monitoring interface..."
    print_status "Flower will be available at: http://localhost:5555"
    celery -A finflow flower
}

# Function to test Celery setup
test_celery() {
    print_header "Testing Celery Setup"
    check_redis
    activate_venv
    cd "$PROJECT_DIR"
    
    print_status "Running Celery test suite..."
    python test_celery.py
}

# Function to show Celery status
show_status() {
    print_header "Celery Status"
    check_redis
    activate_venv
    cd "$PROJECT_DIR"
    
    print_status "Checking Celery worker status..."
    celery -A finflow inspect active
    
    echo ""
    print_status "Checking Celery scheduled tasks..."
    celery -A finflow inspect scheduled
    
    echo ""
    print_status "Checking Celery registered tasks..."
    celery -A finflow inspect registered
}

# Function to run a specific task
run_task() {
    local task_name="$1"
    print_header "Running Task: $task_name"
    check_redis
    activate_venv
    cd "$PROJECT_DIR"
    
    case "$task_name" in
        "analytics")
            print_status "Running portfolio analytics task..."
            python -c "
from finflow.core.tasks import refresh_portfolio_analytics
result = refresh_portfolio_analytics.delay()
print('Task submitted:', result.id)
print('Result:', result.get(timeout=30))
"
            ;;
        "health")
            print_status "Running health check task..."
            python -c "
from finflow.core.tasks import health_check
result = health_check.delay()
print('Task submitted:', result.id)
print('Result:', result.get(timeout=10))
"
            ;;
        "cleanup")
            print_status "Running log cleanup task..."
            python -c "
from finflow.core.tasks import cleanup_old_logs
result = cleanup_old_logs.delay()
print('Task submitted:', result.id)
print('Result:', result.get(timeout=30))
"
            ;;
        "test")
            print_status "Running test task..."
            python -c "
from finflow.core.tasks import test_task
result = test_task.delay('Hello from script!')
print('Task submitted:', result.id)
print('Result:', result.get(timeout=10))
"
            ;;
        *)
            print_error "Unknown task: $task_name"
            print_status "Available tasks: analytics, health, cleanup, test"
            exit 1
            ;;
    esac
}

# Function to show help
show_help() {
    print_header "Celery Management Script"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  worker     Start Celery worker only"
    echo "  beat       Start Celery beat scheduler only"
    echo "  both       Start both worker and beat (recommended)"
    echo "  flower     Start Celery Flower monitoring interface"
    echo "  test       Run Celery test suite"
    echo "  status     Show Celery status and active tasks"
    echo "  run TASK   Run a specific task (analytics, health, cleanup, test)"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 both              # Start worker and beat"
    echo "  $0 run analytics     # Run portfolio analytics task"
    echo "  $0 flower            # Start monitoring interface"
    echo "  $0 status            # Check Celery status"
    echo ""
    echo "Note: Make sure Redis is running before starting Celery services."
}

# Main script logic
case "${1:-help}" in
    "worker")
        start_worker
        ;;
    "beat")
        start_beat
        ;;
    "both")
        start_both
        ;;
    "flower")
        start_flower
        ;;
    "test")
        test_celery
        ;;
    "status")
        show_status
        ;;
    "run")
        if [ -z "$2" ]; then
            print_error "Please specify a task to run"
            print_status "Available tasks: analytics, health, cleanup, test"
            exit 1
        fi
        run_task "$2"
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
