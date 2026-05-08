.PHONY: help up down restart logs build clean test dev prod local

help:
	@echo "╔════════════════════════════════════════╗"
	@echo "║   Avatar Chatbot - Makefile Commands  ║"
	@echo "╠════════════════════════════════════════╣"
	@echo "║  make local    - Start full local env  ║"
	@echo "║  make dev      - Start dev mode       ║"
	@echo "║  make prod     - Start prod mode      ║"
	@echo "║  make up       - Start infrastructure ║"
	@echo "║  make down     - Stop all services    ║"
	@echo "║  make restart  - Restart all          ║"
	@echo "║  make build    - Build all images     ║"
	@echo "║  make logs     - View all logs        ║"
	@echo "║  make test     - Run health checks    ║"
	@echo "║  make clean    - Full cleanup         ║"
	@echo "║  make ps       - List services        ║"
	@echo "╚════════════════════════════════════════╝"

local:
	@bash scripts/start-local.sh

down:
	@bash scripts/stop-local.sh

up:
	docker compose -f docker-compose.yml up -d nats redis postgres qdrant opensearch

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

restart:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml restart

build:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml build

logs:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

test:
	@bash scripts/test-local.sh

ps:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml ps

clean:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v
	docker system prune -f
	@echo "✅ Cleanup complete"

shell-gateway:
	docker compose exec gateway /bin/sh

shell-db:
	docker compose exec postgres psql -U chatbot

nats-listen:
	docker compose exec nats nats sub "session.>"

nats-pub:
	docker compose exec nats nats pub "session.test.asr.final" '{"text":"bonjour","source":"text"}'