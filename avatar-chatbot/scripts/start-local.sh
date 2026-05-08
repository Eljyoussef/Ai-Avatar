#!/bin/bash

set -e

echo "════════════════════════════════════════"
echo "  Avatar Chatbot - Local Development"
echo "════════════════════════════════════════"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed."
    exit 1
fi

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is required."
    exit 1
fi

# Copy env if not exists
if [ ! -f .env ]; then
    cp .env.development .env
    echo "✅ Created .env from .env.development"
fi

echo ""
echo "📦 Step 1: Building Docker images..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml build

echo ""
echo "🚀 Step 2: Starting infrastructure..."
docker compose -f docker-compose.yml up -d nats redis postgres

echo ""
echo "⏳ Waiting for infrastructure to be ready..."
sleep 5

# Check NATS
if curl -s http://localhost:8222 > /dev/null 2>&1; then
    echo "✅ NATS is ready (http://localhost:8222)"
else
    echo "⚠️  NATS may not be ready yet"
fi

# Check Redis
if docker compose exec redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis may not be ready yet"
fi

# Check PostgreSQL
if docker compose exec postgres pg_isready -U chatbot > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "⚠️  PostgreSQL may not be ready yet"
fi

echo ""
echo "🔧 Step 3: Starting core services..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d gateway session-manager

echo ""
echo "🎤 Step 4: Starting AI services..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d \
    accent-router intent-service asr-service tts-service \
    rag-service inference-gateway memory-service document-processor

echo ""
echo "🤖 Step 5: Starting avatar service..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d avatar-adapter

echo ""
echo "📊 Step 6: Starting monitoring..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d \
    prometheus grafana jaeger loki

echo ""
echo "🌐 Step 7: Starting frontend..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d frontend

echo ""
echo "════════════════════════════════════════"
echo "  ✅ All services started!"
echo ""
echo "  📱 Frontend:  http://localhost:3000"
echo "  🔌 API:       http://localhost:8000"
echo "  📊 Grafana:   http://localhost:3001"
echo "  🔍 Jaeger:    http://localhost:16686"
echo "  📡 NATS:      http://localhost:8222"
echo ""
echo "  Run 'docker compose logs -f' to see logs"
echo "  Run './scripts/stop-local.sh' to stop"
echo "════════════════════════════════════════"