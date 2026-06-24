.PHONY: install test lint format run-dev fix build up down logs ps clean monitoring-up monitoring-down migrate migration

build:
	docker compose build

up:
	docker compose up -d
	@echo "✅ All services started"
	@echo "🌐 Frontend:   http://localhost:8501"
	@echo "🔌 API Docs:   http://localhost:8000/docs"
	@echo "🌸 Flower:     http://localhost:5555"
	@echo "📊 MLflow:     http://localhost:5000"

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

clean:
	docker compose down -v --remove-orphans
	docker system prune -f

monitoring-up:
	docker compose -f docker-compose.monitoring.yml up -d
	@echo "📈 Prometheus: http://localhost:9090"
	@echo "📊 Grafana:    http://localhost:3000"

monitoring-down:
	docker compose -f docker-compose.monitoring.yml down

migrate:
	cd shared && alembic upgrade head

migration:
	cd shared && alembic revision --autogenerate -m "$(name)"

install:
	uv pip install -r requirements/dev.txt

test:
	pytest tests/ -v

lint:
	ruff check .

format:
	ruff format .

run-dev:
	docker compose up -d
	uvicorn services.api_gateway.main:app --reload --port 8000
	
fix:
	ruff check . --fix