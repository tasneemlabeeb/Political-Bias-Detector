#!/bin/bash
# Start backend with environment variables from .env file

# Load .env file
set -a
source .env
set +a

# Start backend
PYTHONPATH=. /opt/homebrew/bin/python3.11 -m uvicorn backend.main:app --reload --port 8000
