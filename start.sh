#!/usr/bin/env bash
# GuardPay startup script – builds and runs all services via Docker Compose
set -e

echo "Building Docker images..."
docker compose -f docker-compose.yml build

echo "Starting services..."
# Run in background and attach logs
docker compose -f docker-compose.yml up
