#!/bin/bash
# Startup script for Render to avoid WORKER TIMEOUT and OOM
echo "🚀 Starting Cleo AI Backend with Optimized Gunicorn Config..."

# -w 1: Only 1 worker to save RAM on Render 512MB
# --timeout 120: Longer timeout to allow AI Pool initialization without SIGABRT
# -k uvicorn.workers.UvicornWorker: Standard FastAPI worker
gunicorn -w 1 -k uvicorn.workers.UvicornWorker --timeout 120 --bind 0.0.0.0:$PORT main:app
