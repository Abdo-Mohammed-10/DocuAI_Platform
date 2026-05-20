.PHONY: install test lint format run-dev

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