#!/bin/bash
# Docker Compose Wrapper - handles both v1 (docker-compose) and v2 (docker compose)

# Try docker compose first (v2), fallback to docker-compose (v1)
if command -v docker &> /dev/null; then
    # Check if docker compose works (v2)
    if docker compose version &> /dev/null; then
        docker compose "$@"
    # Fallback to docker-compose (v1)
    elif command -v docker-compose &> /dev/null; then
        docker-compose "$@"
    else
        echo "Error: Docker Compose is not installed"
        exit 1
    fi
else
    echo "Error: Docker is not installed"
    exit 1
fi
