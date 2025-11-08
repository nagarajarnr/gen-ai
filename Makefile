.PHONY: help start stop restart logs build test lint format ingest-sample clean

help: ## Show this help message
	@echo "Accord AI Compliance - Makefile Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

start: ## Start all services
	docker-compose up --build -d
	@echo "Services starting..."
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Mongo Express: http://localhost:8081 (admin/admin123)"
	@sleep 5
	@echo "Services ready!"

stop: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## View logs from all services
	docker-compose logs -f

logs-api: ## View API logs only
	docker-compose logs -f api

logs-mongo: ## View MongoDB logs only
	docker-compose logs -f mongo

build: ## Build Docker images
	docker-compose build

rebuild: ## Rebuild Docker images from scratch
	docker-compose build --no-cache

test: ## Run tests
	docker-compose exec api pytest tests/ -v --cov=app --cov-report=term-missing

test-local: ## Run tests locally (requires local Python env)
	pytest tests/ -v --cov=app --cov-report=html

lint: ## Run linters
	docker-compose exec api flake8 app/ tests/
	docker-compose exec api mypy app/

lint-local: ## Run linters locally
	flake8 app/ tests/
	mypy app/

format: ## Format code with black
	docker-compose exec api black app/ tests/
	docker-compose exec api isort app/ tests/

format-local: ## Format code locally
	black app/ tests/
	isort app/ tests/

ingest-sample: ## Ingest sample documents
	@echo "Waiting for API to be ready..."
	@sleep 5
	docker-compose exec api python scripts/ingest_samples.py

shell-api: ## Open shell in API container
	docker-compose exec api /bin/bash

shell-mongo: ## Open MongoDB shell
	docker-compose exec mongo mongosh accord_compliance

clean: ## Clean up containers, volumes, and temporary files
	docker-compose down -v
	rm -rf storage/*
	rm -rf __pycache__ app/__pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

clean-all: clean ## Clean everything including images
	docker-compose down -v --rmi all

dev: ## Start development environment
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

install: ## Install dependencies locally
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-asyncio black flake8 mypy isort

db-backup: ## Backup MongoDB database
	@mkdir -p backups
	docker-compose exec -T mongo mongodump --db=accord_compliance --archive > backups/backup_$(shell date +%Y%m%d_%H%M%S).archive
	@echo "Backup created in backups/"

db-restore: ## Restore MongoDB database (usage: make db-restore FILE=backup.archive)
	@if [ -z "$(FILE)" ]; then echo "Usage: make db-restore FILE=backup.archive"; exit 1; fi
	docker-compose exec -T mongo mongorestore --db=accord_compliance --archive < $(FILE)

status: ## Show service status
	docker-compose ps

health: ## Check service health
	@echo "Checking API health..."
	@curl -s http://localhost:8000/health || echo "API not responding"
	@echo "\nChecking MongoDB..."
	@docker-compose exec -T mongo mongosh --eval "db.adminCommand('ping')" accord_compliance || echo "MongoDB not responding"

curl-examples: ## Show example curl commands
	@echo "=== Accord AI Compliance - cURL Examples ==="
	@echo ""
	@echo "1. Health Check:"
	@echo "   curl http://localhost:8000/health"
	@echo ""
	@echo "2. Ingest Text:"
	@echo '   curl -X POST "http://localhost:8000/api/v1/ingest/text" \'
	@echo '     -H "Content-Type: application/json" \'
	@echo '     -d '"'"'{"text": "Your compliance text...", "metadata": {"source": "manual"}}'"'"
	@echo ""
	@echo "3. Ingest PDF:"
	@echo '   curl -X POST "http://localhost:8000/api/v1/ingest/pdf" \'
	@echo '     -F "file=@samples/sample_compliance_doc.pdf" \'
	@echo '     -F '"'"'metadata={"department": "legal"}'"'"
	@echo ""
	@echo "4. Ask Question:"
	@echo '   curl -X POST "http://localhost:8000/api/v1/qa" \'
	@echo '     -H "Content-Type: application/json" \'
	@echo '     -d '"'"'{"query": "What are the data retention policies?", "scope": "all"}'"'"
	@echo ""
	@echo "5. List Documents:"
	@echo '   curl http://localhost:8000/api/v1/documents'
	@echo ""

