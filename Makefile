# ========================
# Project Variables
# ========================

VENV_NAME=env_sent
VENV_ACTIVATE=source $(VENV_NAME)/bin/activate
PYTHON=$(VENV_NAME)/bin/python
PIP=$(VENV_NAME)/bin/pip
ENV_FILE=.env

# ========================
# Helpers
# ========================

check-env: ## Install Python dependencies
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "❌ .env file not found!"; \
		exit 1; \
	fi

check-venv: ## Check if virtualenv exists
	@if [ ! -d "$(VENV_NAME)" ]; then \
		echo "❌ Virtualenv $(VENV_NAME) not found. Please create it."; \
		exit 1; \
	fi

load-env: ## Load environment variables from .env file
	@set -a && source $(ENV_FILE) && set +a

# ========================
# Setup and Install
# ========================

install: check-venv ## Install Python dependencies
	@echo "🔹 Installing dependencies..."
	@$(VENV_ACTIVATE) && $(PIP) install -r requirements.txt

# ========================
# Database
# ========================

migrate: check-venv check-env ## Run database migrations
	@echo "🔹 Running database migrations..."
	@$(VENV_ACTIVATE) && $(PYTHON) backend/database/migration_runner.py

backup-db: ## Backup PostgreSQL database
	@mkdir -p backups
	@timestamp=$$(date +"%Y-%m-%d_%H-%M-%S"); \
	docker exec postgres pg_dump -U airflow airflow > backups/backup_$$timestamp.sql && \
	echo "✅ Backup saved to backups/backup_$$timestamp.sql"

# ========================
# Docker (Infrastructure)
# ========================

docker-build:
	docker-compose build --no-cache

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-restart:
	docker-compose down && docker-compose up -d

docker-prune:
	docker system prune -f

docker-start:
	@echo "🔹 Starting services using local images..."
	docker-compose -f local-compose.yml up -d

docker-stop:
	@echo "🔹 Stopping services..."
	docker-compose -f local-compose.yml down

docker-status:
	@echo "🔹 Checking service status..."
	docker-compose -f local-compose.yml ps

docker-logs:
	@echo "🔹 Viewing logs..."
	docker-compose -f local-compose.yml logs -f

# ========================
# Full Safe Startup
# ========================

up:
	@echo "🔌 Starting PostgreSQL only..."
	docker-compose up -d postgres

	@echo "⏳ Waiting for PostgreSQL to be ready..."
	@count=0; until docker exec postgres pg_isready -U airflow > /dev/null 2>&1; do \
		if [ $$count -ge 30 ]; then \
			echo "❌ Postgres did not become ready in time."; \
			exit 1; \
		fi; \
		echo "🔄 Waiting... ($$count)"; \
		count=$$((count + 1)); \
		sleep 2; \
	done
	@echo "✅ PostgreSQL is ready."

	@echo "🧪 Checking if Airflow DB is initialized..."
	docker-compose run --rm airflow_webserver bash -c '\
	if airflow db check 2>&1 | grep -q "Connection is ok"; then \
		echo "✅ Airflow DB is already initialized."; \
	else \
		echo "🚀 Initializing Airflow DB..."; \
		airflow db init; \
	fi'

	@echo "🚀 Starting all remaining services..."
	docker-compose up -d

# ========================
# Backend Development
# ========================

backend-dev: check-venv check-env
	@echo "🔹 Starting FastAPI app with uvicorn..."
	@$(VENV_ACTIVATE) && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# ========================
# Tests
# ========================

test: check-venv check-env
	@echo "🔹 Running unit tests..."
	@$(VENV_ACTIVATE) && pytest backend/tests/

# ========================
# Airflow Utilities
# ========================

airflow-init:
	docker-compose run --rm airflow_webserver airflow db init

airflow-version:
	docker-compose run --rm airflow_webserver airflow version

bootstrap-airflow:
	@echo "📦 Waiting for PostgreSQL to be ready..."
	@until docker exec postgres pg_isready -U airflow > /dev/null 2>&1; do \
		sleep 1; \
	done
	@echo "🚀 Initializing Airflow DB..."
	docker-compose run --rm airflow_webserver airflow db init
	@echo "🔄 Restarting Airflow services..."
	docker-compose restart airflow_scheduler airflow_webserver airflow_worker
	@echo "✅ Airflow bootstrapped successfully."

# ========================
# Health Check
# ========================

health-check:
	@echo "🔎 Checking backend..."
	@curl -s http://localhost:8000/health || echo "❌ Backend not responding"

	@echo "🔎 Checking Airflow UI..."
	@curl -s --head http://localhost:8080 | head -n 1 || echo "❌ Airflow UI not responding"

	@echo "🔎 Checking PostgreSQL container..."
	@docker exec postgres pg_isready -U airflow || echo "❌ Postgres not ready"


kill-all: ## Kill all containers
	@echo "⚠️  WARNING: This will delete ALL containers, volumes, and networks."
	@read -p "Are you in a dev environment and sure you want to continue? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		echo "🧨 Stopping and removing everything..."; \
		docker-compose down -v --remove-orphans; \
		docker system prune -f; \
		echo "✅ Done. Everything removed."; \
	else \
		echo "❌ Aborted."; \
	fi


# ========================
# Help
# ========================

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "🔹 \033[36m%-22s\033[0m %s\n", $$1, $$2}'
