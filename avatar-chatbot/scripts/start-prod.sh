#!/bin/bash

echo "🚀 Starting Avatar Chatbot (Production Mode)"

# Check for .env.production
if [ ! -f .env.production ]; then
    echo "❌ .env.production not found!"
    exit 1
fi

# Load production env
set -a
source .env.production
set +a

# Pull latest images
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull

# Start services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Wait for healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Run healthcheck
./scripts/healthcheck.sh

echo "✅ Production environment ready!"