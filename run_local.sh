#!/bin/bash
# Local development server script
# Loads .env and runs the API server with scheduler disabled

set -a
source .env
set +a

echo "Starting local dev server (scheduler disabled)..."
uvicorn app.main:app --reload --port 8000
