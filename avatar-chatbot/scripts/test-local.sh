#!/bin/bash

echo "🧪 Testing Avatar Chatbot locally..."
echo ""

# Test Gateway
echo "1. Testing Gateway..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "   ✅ Gateway is healthy"
else
    echo "   ❌ Gateway is not responding"
fi

# Test Frontend
echo "2. Testing Frontend..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    echo "   ✅ Frontend is responding"
else
    echo "   ❌ Frontend is not responding"
fi

# Test NATS monitoring
echo "3. Testing NATS..."
if curl -s http://localhost:8222/varz | grep -q "server_name"; then
    echo "   ✅ NATS is healthy"
else
    echo "   ❌ NATS is not responding"
fi

# Test Qdrant
echo "4. Testing Qdrant..."
if curl -s http://localhost:6333/collections | grep -q "collections"; then
    echo "   ✅ Qdrant is healthy"
else
    echo "   ❌ Qdrant is not responding"
fi

# Test OpenSearch
echo "5. Testing OpenSearch..."
if curl -s http://localhost:9200 | grep -q "cluster_name"; then
    echo "   ✅ OpenSearch is healthy"
else
    echo "   ❌ OpenSearch is not responding"
fi

echo ""
echo "════════════════════════════════════════"
echo "  Health check complete!"
echo "════════════════════════════════════════"