#!/bin/bash

echo "🛑 Stopping Avatar Chatbot..."

docker compose -f docker-compose.yml -f docker-compose.dev.yml down

echo "✅ All services stopped"