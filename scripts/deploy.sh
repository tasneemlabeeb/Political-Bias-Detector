#!/bin/bash

# Political Bias Detector - Deployment Script
# Usage: ./scripts/deploy.sh [up|down|logs|build|restart]

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Political Bias Detector - Deployment Tool${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    echo ""
}

print_error() {
    echo -e "${RED}✗ Error: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_prerequisites() {
    print_header
    echo "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker found: $(docker --version)"
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    print_success "Docker Compose found: $(docker-compose --version)"
    
    if [ ! -f "$PROJECT_DIR/$ENV_FILE" ]; then
        print_warning "Production environment file not found"
        echo "Creating from template..."
        cp "$PROJECT_DIR/.env.production.example" "$PROJECT_DIR/$ENV_FILE"
        print_warning "Please edit $ENV_FILE with your configuration"
        exit 1
    fi
    
    print_success "All prerequisites met"
    echo ""
}

build_images() {
    echo "Building Docker images..."
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    print_success "Images built successfully"
}

start_services() {
    echo "Starting services..."
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" up -d
    
    echo "Waiting for services to be ready..."
    sleep 10
    
    # Check health
    if curl -s http://localhost/health > /dev/null; then
        print_success "Services started successfully"
        print_success "Frontend: http://10.122.0.3"
        print_success "API Docs: http://10.122.0.3/api/docs"
    else
        print_warning "Services started but health check failed"
        echo "Check logs with: docker-compose -f $COMPOSE_FILE logs"
    fi
}

stop_services() {
    echo "Stopping services..."
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" down
    print_success "Services stopped"
}

show_logs() {
    cd "$PROJECT_DIR"
    SERVICE=${1:-}
    if [ -z "$SERVICE" ]; then
        docker-compose -f "$COMPOSE_FILE" logs -f
    else
        docker-compose -f "$COMPOSE_FILE" logs -f "$SERVICE"
    fi
}

restart_services() {
    echo "Restarting services..."
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" restart
    print_success "Services restarted"
}

show_status() {
    print_header
    echo "Service Status:"
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    echo "Resource Usage:"
    docker stats --no-stream
}

clean_volumes() {
    print_warning "This will remove all data in containers"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        cd "$PROJECT_DIR"
        docker-compose -f "$COMPOSE_FILE" down -v
        print_success "Volumes cleaned"
    else
        print_warning "Operation cancelled"
    fi
}

backup_database() {
    BACKUP_DIR="$PROJECT_DIR/backups"
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    
    echo "Backing up database to $BACKUP_FILE..."
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U pbd_user political_bias_detector > "$BACKUP_FILE"
    
    print_success "Database backed up"
    echo "Size: $(du -h $BACKUP_FILE | cut -f1)"
}

show_help() {
    cat <<EOF
Usage: $0 [COMMAND]

Commands:
    up              Start all services
    down            Stop all services
    build           Build Docker images
    restart         Restart services
    logs [SERVICE]  Show service logs (SERVICE: backend, frontend, nginx, postgres)
    status          Show service status and resource usage
    clean           Remove volumes and data
    backup          Backup database
    health          Check service health
    help            Show this help message

Examples:
    $0 up
    $0 logs backend
    $0 logs
    $0 restart
    $0 backup

EOF
}

health_check() {
    print_header
    echo "Running health checks..."
    
    endpoints=(
        "http://localhost/health"
        "http://localhost/api/docs"
        "http://localhost"
    )
    
    for url in "${endpoints[@]}"; do
        if curl -s "$url" > /dev/null 2>&1; then
            print_success "$url is healthy"
        else
            print_error "$url is unreachable"
        fi
    done
}

# Main script logic
main() {
    COMMAND="${1:-help}"
    
    case "$COMMAND" in
        up)
            check_prerequisites
            start_services
            ;;
        down)
            stop_services
            ;;
        build)
            check_prerequisites
            build_images
            ;;
        restart)
            restart_services
            ;;
        logs)
            show_logs "$2"
            ;;
        status)
            show_status
            ;;
        clean)
            clean_volumes
            ;;
        backup)
            backup_database
            ;;
        health)
            health_check
            ;;
        help)
            show_help
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
