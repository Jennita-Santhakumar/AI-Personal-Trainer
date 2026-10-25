.PHONY: install dev test lint migrate seed docker-up docker-down clean

install:
	pip install -r requirements.txt

install-test:
	pip install -r requirements.txt -r requirements-test.txt

dev:
	uvicorn main:app --reload --port 8000

worker:
	celery -A tasks worker --loglevel=info --concurrency=4

beat:
	celery -A tasks beat --loglevel=info

test-unit:
	pytest tests/unit/ -v --tb=short

test-integration:
	pytest tests/integration/ -v --tb=short

test:
	pytest tests/ -v --tb=short --cov=. --cov-report=term-missing

lint:
	ruff check . --fix
	ruff format .

migrate:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

seed:
	python scripts/seed_db.py

docker-up:
	docker-compose up -d postgres redis influxdb minio

docker-down:
	docker-compose down

docker-build:
	docker-compose build

docker-all:
	docker-compose up --build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
	rm -rf .pytest_cache htmlcov .coverage 2>/dev/null; true
