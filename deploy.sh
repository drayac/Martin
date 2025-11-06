#!/bin/bash

# Martin Psychology App - Deployment Script
# This script automates the deployment of the psychology app using Docker Compose

set -e  # Exit on any error

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if docker compose is available (either as plugin or standalone)
    if ! docker compose version >/dev/null 2>&1 && ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found"
        if [ -f ".env.example" ]; then
            print_status "Copying .env.example to .env"
            cp .env.example .env
            print_warning "Please edit .env file and add your Groq API key before proceeding"
            print_status "Run: nano .env"
            exit 1
        else
            print_error ".env.example file not found. Cannot create .env file."
            exit 1
        fi
    fi
    
    # Check if API key is set
    if grep -q "your_groq_api_key_here" .env; then
        print_error "Please set your actual Groq API key in .env file"
        print_status "Edit .env and replace 'your_groq_api_key_here' with your actual API key"
        exit 1
    fi
    
    print_success ".env file configured"
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p data
    mkdir -p sounds
    mkdir -p images
    
    print_success "Directories created"
}

# Function to build and start the application
start_application() {
    print_status "Building and starting the application..."
    
    # Stop any existing containers
    docker compose down 2>/dev/null || true
    
    # Build and start
    docker compose up -d --build
    
    print_success "Application started"
}

# Function to check application health
check_health() {
    print_status "Checking application health..."
    
    # Wait for application to start
    sleep 10
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8532/_stcore/health >/dev/null 2>&1; then
            print_success "Application is healthy and running"
            print_status "Access the application at: http://localhost:8532"
            return 0
        fi
        
        print_status "Waiting for application to start... (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "Application health check failed"
    print_status "Check logs with: docker compose logs martin-psychology-app"
    return 1
}

# Function to show logs
show_logs() {
    print_status "Showing application logs..."
    docker compose logs -f martin-psychology-app
}

# Function to stop the application
stop_application() {
    print_status "Stopping the application..."
    docker compose down
    print_success "Application stopped"
}

# Function to show status
show_status() {
    print_status "Application status:"
    docker compose ps
}

# Main menu
show_menu() {
    echo ""
    echo "Martin Psychology App - Deployment Manager"
    echo "=========================================="
    echo "1. Deploy application"
    echo "2. Stop application"
    echo "3. Restart application"
    echo "4. Show logs"
    echo "5. Show status"
    echo "6. Update application"
    echo "7. Exit"
    echo ""
}

# Deploy function
deploy() {
    check_prerequisites
    check_env_file
    create_directories
    start_application
    check_health
}

# Update function
update() {
    print_status "Updating application..."
    docker compose down
    docker compose build --no-cache
    docker compose up -d
    check_health
}

# Restart function
restart() {
    print_status "Restarting application..."
    docker compose restart
    check_health
}

# Main script logic
if [ $# -eq 0 ]; then
    # Interactive mode
    while true; do
        show_menu
        read -p "Please select an option (1-7): " choice
        
        case $choice in
            1)
                deploy
                ;;
            2)
                stop_application
                ;;
            3)
                restart
                ;;
            4)
                show_logs
                ;;
            5)
                show_status
                ;;
            6)
                update
                ;;
            7)
                print_status "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid option. Please select 1-7."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
else
    # Command line mode
    case $1 in
        deploy)
            deploy
            ;;
        stop)
            stop_application
            ;;
        restart)
            restart
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        update)
            update
            ;;
        *)
            echo "Usage: $0 [deploy|stop|restart|logs|status|update]"
            echo "Run without arguments for interactive mode"
            exit 1
            ;;
    esac
fi