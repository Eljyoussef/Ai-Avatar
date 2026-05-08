#!/bin/bash

echo "🏥 Running health checks..."

services=(
    "gateway:8000/health"
    "nats:8222"
    "qdrant:6333"
    "opensearch:9200"
    "prometheus:9090"
    "grafana:3000"
    "jaeger:16686"
)

for service in "${services[@]}"; do
    IFS=':' read -r host port_path <<< "$service"
    
    if curl -s "http://$host:$port_path" > /dev/null 2>&1; then
        echo "✅ $host is healthy"
    else
        echo "❌ $host is DOWN"
    fi
done