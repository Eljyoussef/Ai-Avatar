Write-Host "Stopping all services..." -ForegroundColor Yellow
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
Write-Host "All services stopped." -ForegroundColor Green