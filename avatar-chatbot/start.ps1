Write-Host "Starting Avatar Chatbot..." -ForegroundColor Cyan

# Create .env if missing
if (-not (Test-Path .env)) { Copy-Item .env.development .env }

# Start everything with ONE command
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

Write-Host "Waiting for services..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "SERVICES:" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  API:      http://localhost:8000/health" -ForegroundColor White
Write-Host "  NATS:     http://localhost:8222" -ForegroundColor White
Write-Host ""

# Quick test
try { 
    $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "Gateway: ONLINE" -ForegroundColor Green 
} catch { 
    Write-Host "Gateway: starting up..." -ForegroundColor Yellow 
}

try { 
    $r = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
    Write-Host "Frontend: ONLINE" -ForegroundColor Green 
} catch { 
    Write-Host "Frontend: starting up..." -ForegroundColor Yellow 
}

Write-Host ""
Write-Host "Open http://localhost:3000 in your browser!" -ForegroundColor Cyan
Write-Host "Logs: docker compose logs -f" -ForegroundColor Gray