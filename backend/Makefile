# WhatsApp Customer Agent - Development Makefile
# Provides common development tasks and automation

.PHONY: help install test lint format security clean dev build deploy docs

# Default target
help:
	@echo "WhatsApp Customer Agent - Development Commands"
	@echo "=============================================="
	@echo "Setup Commands:"
	@echo "  install        Install all dependencies"
	@echo "  install-dev    Install development dependencies"
	@echo "  install-pre-commit Install and setup pre-commit hooks"
	@echo ""
	@echo "Development Commands:"
	@echo "  dev            Start development server with hot reload"
	@echo "  dev-db         Start development database (PostgreSQL)"
	@echo "  dev-redis      Start development Redis"
	@echo "  dev-full       Start all development services"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test           Run all tests"
	@echo "  test-unit      Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-e2e       Run end-to-end tests only"
	@echo "  test-coverage  Run tests with coverage report"
	@echo "  test-watch     Run tests in watch mode"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  lint           Run all linters"
	@echo "  format         Format code"
	@echo "  security       Run security scans"
	@echo "  type-check     Run type checking"
	@echo "  pre-commit     Run pre-commit hooks"
	@echo ""
	@echo "Database Commands:"
	@echo "  db-migrate     Run database migrations"
	@echo "  db-upgrade     Upgrade database to latest"
	@echo "  db-downgrade   Downgrade database one version"
	@echo "  db-reset       Reset database (DESTRUCTIVE)"
	@echo "  db-seed        Seed database with test data"
	@echo ""
	@echo "Build Commands:"
	@echo "  build          Build Docker image"
	@echo "  build-prod     Build production Docker image"
	@echo ""
	@echo "Documentation Commands:"
	@echo "  docs           Generate API documentation"
	@echo "  docs-serve     Serve documentation locally"
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean          Clean temporary files"
	@echo "  clean-all      Clean everything including venv"
	@echo "  check-deps     Check for outdated dependencies"
	@echo "  update-deps    Update dependencies"

# Installation Commands
install:
	@echo "Installing dependencies..."
	poetry install --no-root

install-dev:
	@echo "Installing development dependencies..."
	poetry install --no-root --with dev

install-pre-commit:
	@echo "Installing pre-commit hooks..."
	poetry run pre-commit install
	poetry run pre-commit install --hook-type commit-msg

# Development Commands
dev:
	@echo "Starting development server..."
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-db:
	@echo "Starting PostgreSQL development database..."
	docker run --name whatsapp-agent-db -d \
		-e POSTGRES_USER=postgres \
		-e POSTGRES_PASSWORD=postgres \
		-e POSTGRES_DB=whatsapp_agent_dev \
		-p 5432:5432 \
		postgres:15-alpine || docker start whatsapp-agent-db

dev-redis:
	@echo "Starting Redis development server..."
	docker run --name whatsapp-agent-redis -d \
		-p 6379:6379 \
		redis:7-alpine || docker start whatsapp-agent-redis

dev-full: dev-db dev-redis
	@echo "All development services started"
	@sleep 3
	@make dev

# Testing Commands
test:
	@echo "Running all tests..."
	poetry run pytest -v --cov=app --cov-report=term-missing --cov-report=html

test-unit:
	@echo "Running unit tests..."
	poetry run pytest tests/unit/ -v

test-integration:
	@echo "Running integration tests..."
	poetry run pytest tests/integration/ -v

test-e2e:
	@echo "Running end-to-end tests..."
	poetry run pytest tests/e2e/ -v

test-coverage:
	@echo "Running tests with detailed coverage..."
	poetry run pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml --cov-fail-under=80

test-watch:
	@echo "Running tests in watch mode..."
	poetry run ptw -- --testmon

test-performance:
	@echo "Running performance tests..."
	poetry run pytest tests/performance/ -v --benchmark-json=benchmark.json

# Code Quality Commands
lint:
	@echo "Running linters..."
	poetry run flake8 app tests
	poetry run isort --check-only app tests
	poetry run black --check app tests

format:
	@echo "Formatting code..."
	poetry run isort app tests
	poetry run black app tests
	poetry run autoflake --in-place --remove-all-unused-imports --remove-unused-variables --expand-star-imports --recursive app tests

security:
	@echo "Running security scans..."
	poetry run bandit -r app/ -f json -o bandit-report.json
	poetry run safety check
	python scripts/detect_secrets.py

type-check:
	@echo "Running type checking..."
	poetry run mypy app --ignore-missing-imports

pre-commit:
	@echo "Running pre-commit hooks..."
	poetry run pre-commit run --all-files

# Database Commands
db-migrate:
	@echo "Creating new migration..."
	poetry run alembic revision --autogenerate -m "$(shell read -p 'Migration message: ' msg; echo $$msg)"

db-upgrade:
	@echo "Upgrading database..."
	poetry run alembic upgrade head

db-downgrade:
	@echo "Downgrading database..."
	poetry run alembic downgrade -1

db-reset:
	@echo "Resetting database (DESTRUCTIVE)..."
	@read -p "Are you sure? This will delete all data [y/N]: " confirm && [ "$$confirm" = "y" ]
	poetry run alembic downgrade base
	poetry run alembic upgrade head

db-seed:
	@echo "Seeding database with test data..."
	poetry run python scripts/seed_database.py

db-check:
	@echo "Checking database migrations..."
	python scripts/check_migrations.py

# Build Commands
build:
	@echo "Building Docker image..."
	docker build -t whatsapp-agent:latest .

build-prod:
	@echo "Building production Docker image..."
	docker build -f Dockerfile.prod -t whatsapp-agent:prod .

# Documentation Commands
docs:
	@echo "Generating API documentation..."
	poetry run python scripts/generate_api_docs.py

docs-serve:
	@echo "Serving documentation..."
	cd docs && python -m http.server 8080

validate-api:
	@echo "Validating OpenAPI schema..."
	python scripts/validate_openapi.py

# Utility Commands
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*~" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml
	rm -rf dist/ build/
	rm -f *.log

clean-all: clean
	@echo "Cleaning everything including virtual environment..."
	rm -rf .venv/
	docker stop whatsapp-agent-db whatsapp-agent-redis 2>/dev/null || true
	docker rm whatsapp-agent-db whatsapp-agent-redis 2>/dev/null || true

check-deps:
	@echo "Checking for outdated dependencies..."
	poetry show --outdated

update-deps:
	@echo "Updating dependencies..."
	poetry update

# CI/CD Simulation
ci-check: install-dev lint type-check security test-coverage validate-api
	@echo "All CI checks passed! ✅"

ci-test: install-dev test-coverage
	@echo "CI tests completed! ✅"

# Health checks
health-check:
	@echo "Running health checks..."
	curl -f http://localhost:8000/health || exit 1
	curl -f http://localhost:8000/health/db || exit 1
	curl -f http://localhost:8000/health/detailed || exit 1

# Load testing
load-test:
	@echo "Running load tests..."
	poetry run locust -f tests/load/locustfile.py --host http://localhost:8000

# Deployment helpers
deploy-staging:
	@echo "Deploying to staging..."
	docker-compose -f docker-compose.staging.yml up -d

deploy-prod:
	@echo "Deploying to production..."
	@echo "This should be handled by CI/CD pipeline"
	@exit 1

# Development shortcuts
quick-test:
	@echo "Running quick test suite..."
	poetry run pytest tests/unit/ -x --tb=short

watch-logs:
	@echo "Watching application logs..."
	tail -f logs/app.log

# Environment setup
setup-env:
	@echo "Setting up environment files..."
	cp .env.example .env
	@echo "Please edit .env with your configuration"

# Performance monitoring
monitor-performance:
	@echo "Monitoring application performance..."
	poetry run python scripts/monitor_performance.py

# Database utilities
db-backup:
	@echo "Backing up database..."
	docker exec whatsapp-agent-db pg_dump -U postgres whatsapp_agent_dev > backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore:
	@echo "Restoring database from backup..."
	@read -p "Backup file path: " backup_file; \
	docker exec -i whatsapp-agent-db psql -U postgres whatsapp_agent_dev < "$$backup_file"

# Maintenance tasks
maintenance:
	@echo "Running maintenance tasks..."
	@make clean
	@make security
	@make check-deps
	@echo "Maintenance completed! ✅"