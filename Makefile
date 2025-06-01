# ========================
# Enterprise Scraping System - Unified Makefile
# ========================

.PHONY: up up-dev up-prod down status logs clean help
.PHONY: install test migrate backup shell debug deploy

# ========================
# Environment Configuration
# ========================

# Default environment variables (avoid Docker warnings)
export HTTP_PROXY ?= 
export HTTPS_PROXY ?= 
export PROXY_ENABLED ?= false
export SENTRY_DSN ?= 
export ENVIRONMENT ?= development

# Project configuration
VENV_NAME=env_sent
VENV_ACTIVATE=source $(VENV_NAME)/bin/activate
PYTHON=$(VENV_NAME)/bin/python
PIP=$(VENV_NAME)/bin/pip

# ========================
# Quick Start Commands
# ========================

up: up-dev ## 🚀 Start complete system (development mode)

up-dev: ## 🛠️ Start development environment with all services
	@echo "🚀 Starting Enterprise Scraping System (Development)"
	@echo "=================================================="
	@$(MAKE) --no-print-directory _setup-dirs
	@$(MAKE) --no-print-directory _setup-configs
	@$(MAKE) --no-print-directory _check-env
	@echo "🔌 Starting PostgreSQL..."
	@docker-compose up -d postgres
	@$(MAKE) --no-print-directory _wait-postgres
	@echo "📦 Installing dependencies in containers..."
	@$(MAKE) --no-print-directory _install-deps-quiet
	@echo "🧪 Initializing Airflow..."
	@$(MAKE) --no-print-directory _init-airflow
	@echo "🚀 Starting all services..."
	@docker-compose up -d
	@echo "⏳ Waiting for services to be ready..."
	@sleep 20
	@$(MAKE) --no-print-directory status
	@echo ""
	@echo "🎉 System Started Successfully!"
	@$(MAKE) --no-print-directory _show-urls

up-prod: ## 🏭 Start production environment with monitoring
	@echo "🏭 Starting Enterprise Scraping System (Production)"
	@echo "================================================="
	@export ENVIRONMENT=production
	@$(MAKE) --no-print-directory _setup-dirs
	@$(MAKE) --no-print-directory _setup-configs
	@$(MAKE) --no-print-directory _check-env
	@$(MAKE) --no-print-directory _backup-before-start
	@echo "🔌 Starting PostgreSQL..."
	@docker-compose up -d postgres
	@$(MAKE) --no-print-directory _wait-postgres
	@echo "📦 Installing dependencies..."
	@$(MAKE) --no-print-directory _install-deps-quiet
	@echo "🧪 Initializing Airflow..."
	@$(MAKE) --no-print-directory _init-airflow
	@echo "🚀 Starting all services..."
	@docker-compose up -d
	@echo "⏳ Waiting for services..."
	@sleep 30
	@$(MAKE) --no-print-directory status
	@$(MAKE) --no-print-directory _show-urls

down: ## 🛑 Stop all services
	@echo "🛑 Stopping all services..."
	@docker-compose down
	@echo "✅ All services stopped"

# ========================
# System Management
# ========================

status: ## 📊 Check system health and show access URLs
	@echo "📊 Enterprise System Status"
	@echo "=========================="
	@echo ""
	@echo "🐳 Service Status:"
	@docker-compose ps
	@echo ""
	@echo "🌐 Health Checks:"
	@printf "  %-20s " "Airflow:"
	@if curl -s http://localhost:8080/health >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi
	@printf "  %-20s " "Backend API:"
	@if curl -s http://localhost:8000/health >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi
	@printf "  %-20s " "MLflow:"
	@if curl -s http://localhost:5001 >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi
	@printf "  %-20s " "Grafana:"
	@if curl -s http://localhost:3000/api/health >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi
	@printf "  %-20s " "Prometheus:"
	@if curl -s http://localhost:9090/-/healthy >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi
	@printf "  %-20s " "PostgreSQL:"
	@if docker exec postgres pg_isready -U airflow >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi
	@echo ""
	@echo "🗄️ Data Status:"
	@printf "  %-20s " "MLflow Database:"
	@if [ -f "data/mlflow/mlflow.db" ]; then \
		size=$$(du -h data/mlflow/mlflow.db 2>/dev/null | cut -f1); \
		echo "✅ $$size"; \
	else \
		echo "❌ Not Found"; \
	fi
	@printf "  %-20s " "Artifacts:"
	@if [ -d "mlflow_data/artifacts" ]; then \
		count=$$(find mlflow_data/artifacts -type f 2>/dev/null | wc -l | tr -d ' '); \
		echo "✅ $$count files"; \
	else \
		echo "❌ Not Found"; \
	fi

logs: ## 📝 Show logs from all services
	@docker-compose logs -f --tail=50

logs-airflow: ## 📝 Show Airflow logs only
	@docker-compose logs -f airflow_webserver airflow_scheduler

logs-backend: ## 📝 Show Backend API logs only
	@docker-compose logs -f backend

logs-mlflow: ## 📝 Show MLflow logs only
	@docker-compose logs -f mlflow

# ========================
# Development Commands
# ========================

install: ## 📦 Install Python dependencies locally (dev)
	@if [ ! -d "$(VENV_NAME)" ]; then \
		echo "❌ Virtual environment not found. Create with: python -m venv $(VENV_NAME)"; \
		exit 1; \
	fi
	@echo "📦 Installing local dependencies..."
	@$(VENV_ACTIVATE) && $(PIP) install --upgrade pip
	@$(VENV_ACTIVATE) && $(PIP) install -r requirements.txt
	@echo "✅ Dependencies installed"

backend-dev: ## 🛠️ Start backend in development mode (local)
	@if [ ! -d "$(VENV_NAME)" ]; then \
		echo "❌ Virtual environment not found. Run 'make install' first"; \
		exit 1; \
	fi
	@echo "🔹 Starting FastAPI backend locally..."
	@$(VENV_ACTIVATE) && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

test: ## 🧪 Run tests (dev)
	@echo "🧪 Running tests..."
	@$(VENV_ACTIVATE) && pytest backend/tests/ -v

shell: ## 🐚 Open Airflow container shell (dev)
	@docker-compose exec airflow_webserver bash

debug: ## 🐛 Debug Airflow DAG imports and dependencies
	@echo "🐛 Debugging Airflow setup..."
	@docker-compose run --rm airflow_webserver bash -c '\
		export PYTHONPATH="/opt/airflow:/opt/airflow/backend:$$PYTHONPATH"; \
		echo "🐍 Python Path:"; python -c "import sys; [print(p) for p in sys.path]"; \
		echo ""; echo "🧪 Testing imports:"; \
		python -c "import sentry_sdk; print(\"✅ sentry_sdk\")" || echo "❌ sentry_sdk failed"; \
		python -c "import mlflow; print(\"✅ mlflow\")" || echo "❌ mlflow failed"; \
		python -c "from backend.services.app_management_service import AppManagementService; print(\"✅ backend imports\")" || echo "❌ backend imports failed"; \
		echo ""; echo "📋 DAGs:"; airflow dags list 2>&1 | head -10; \
	'

# ========================
# Database Management
# ========================

migrate: ## 🗄️ Run database migrations
	@echo "🗄️ Running database migrations..."
	@if [ -d "$(VENV_NAME)" ]; then \
		$(VENV_ACTIVATE) && $(PYTHON) backend/database/migration_runner.py; \
	else \
		docker-compose exec backend python -c "import asyncio; from backend.database.migration_runner import run_migrations; asyncio.run(run_migrations())"; \
	fi

backup: ## 💾 Backup all persistent data
	@echo "💾 Creating system backup..."
	@timestamp=$$(date +"%Y-%m-%d_%H-%M-%S"); \
	backup_dir="backups/system_$$timestamp"; \
	mkdir -p "$$backup_dir"; \
	echo "📁 Backing up PostgreSQL..."; \
	docker exec postgres pg_dump -U airflow airflow > "$$backup_dir/postgres_backup.sql" 2>/dev/null || echo "  ⚠️ PostgreSQL backup failed"; \
	echo "📁 Backing up MLflow..."; \
	[ -f "data/mlflow/mlflow.db" ] && cp data/mlflow/mlflow.db "$$backup_dir/" || echo "  ⚠️ No MLflow database found"; \
	echo "📁 Backing up artifacts..."; \
	[ -d "mlflow_data" ] && cp -r mlflow_data "$$backup_dir/" || echo "  ⚠️ No artifacts found"; \
	echo "📁 Backing up configs..."; \
	cp .env "$$backup_dir/" 2>/dev/null || echo "  ⚠️ No .env file"; \
	echo "✅ Backup created: $$backup_dir"

# ========================
# Production Deployment
# ========================

deploy-fresh: ## 🆕 Fresh deployment setup (new server)
	@echo "🆕 Fresh Production Deployment"
	@echo "============================="
	@$(MAKE) --no-print-directory _setup-dirs
	@$(MAKE) --no-print-directory _check-deployment
	@echo ""
	@read -p "Environment ready. Start production deployment? (y/n): " confirm; \
	if [ "$$confirm" = "y" ]; then \
		$(MAKE) --no-print-directory up-prod; \
	else \
		echo "❌ Deployment cancelled"; \
	fi

deploy-update: ## 🔄 Update existing deployment (preserves data)
	@echo "🔄 Updating Production Deployment"
	@echo "================================"
	@$(MAKE) --no-print-directory backup
	@echo "📦 Pulling latest images..."
	@docker-compose pull
	@echo "🔄 Restarting services..."
	@docker-compose up -d
	@sleep 20
	@$(MAKE) --no-print-directory status
	@echo "✅ Update complete"

# ========================
# Maintenance Commands
# ========================

clean: ## 🧹 Clean up containers and volumes
	@echo "⚠️  This will remove all containers and volumes!"
	@read -p "Continue? (y/n): " confirm; \
	if [ "$$confirm" = "y" ]; then \
		docker-compose down -v; \
		docker system prune -f; \
		echo "✅ Cleanup complete"; \
	else \
		echo "❌ Cancelled"; \
	fi

restart: ## 🔄 Restart all services
	@echo "🔄 Restarting all services..."
	@docker-compose restart
	@sleep 15
	@$(MAKE) --no-print-directory status

restart-airflow: ## 🔄 Restart Airflow services only
	@docker-compose restart airflow_webserver airflow_scheduler

restart-backend: ## 🔄 Restart Backend service only
	@docker-compose restart backend

restart-mlflow: ## 🔄 Restart MLflow service only
	@docker-compose restart mlflow

# ========================
# Internal Helper Functions
# ========================

_setup-dirs:
	@echo "📁 Creating required directories..."
	@mkdir -p data/mlflow
	@mkdir -p mlflow_data/artifacts
	@mkdir -p mlflow_data/models
	@mkdir -p logs
	@mkdir -p backups
	@mkdir -p backend/airflow/dags
	@mkdir -p backend/airflow/plugins
	@mkdir -p backend/airflow/logs
	@mkdir -p backend/monitoring/prometheus
	@mkdir -p backend/monitoring/grafana/dashboards
	@mkdir -p backend/monitoring/grafana/provisioning/datasources
	@mkdir -p backend/monitoring/grafana/provisioning/dashboards
	@chmod -R 755 data mlflow_data logs backups backend/airflow backend/monitoring >/dev/null 2>&1 || true
	@echo "✅ All directories created"

_setup-configs:
	@echo "⚙️ Creating default configuration files..."
	@if [ ! -f "backend/monitoring/prometheus/prometheus.yml" ]; then \
		printf "global:\n  scrape_interval: 15s\n  evaluation_interval: 15s\n\nscrape_configs:\n  - job_name: 'prometheus'\n    static_configs:\n      - targets: ['localhost:9090']\n\n  - job_name: 'airflow'\n    static_configs:\n      - targets: ['airflow_webserver:8080']\n    metrics_path: '/admin/metrics'\n    scrape_interval: 30s\n\n  - job_name: 'backend'\n    static_configs:\n      - targets: ['backend:8000']\n    metrics_path: '/metrics'\n    scrape_interval: 30s\n" > backend/monitoring/prometheus/prometheus.yml; \
		echo "✅ Created Prometheus config"; \
	fi
	@if [ ! -f "backend/monitoring/grafana/grafana.ini" ]; then \
		printf "[analytics]\ncheck_for_updates = true\n\n[log]\nmode = console\nlevel = info\n\n[paths]\ndata = /var/lib/grafana\nlogs = /var/log/grafana\nplugins = /var/lib/grafana/plugins\nprovisioning = /etc/grafana/provisioning\n\n[server]\nprotocol = http\nhttp_port = 3000\ndomain = localhost\nroot_url = http://localhost:3000\n\n[database]\ntype = sqlite3\npath = grafana.db\n\n[security]\nadmin_user = admin\nadmin_password = admin\n\n[users]\nallow_sign_up = false\n" > backend/monitoring/grafana/grafana.ini; \
		echo "✅ Created Grafana config"; \
	fi
	@if [ ! -f "backend/monitoring/grafana/provisioning/datasources/datasources.yml" ]; then \
		printf "apiVersion: 1\n\ndatasources:\n  - name: Prometheus\n    type: prometheus\n    access: proxy\n    url: http://prometheus:9090\n    isDefault: true\n    editable: true\n\n  - name: PostgreSQL\n    type: postgres\n    access: proxy\n    url: postgres:5432\n    database: airflow\n    user: airflow\n    secureJsonData:\n      password: airflow\n    jsonData:\n      sslmode: disable\n      postgresVersion: 1300\n    editable: true\n" > backend/monitoring/grafana/provisioning/datasources/datasources.yml; \
		echo "✅ Created Grafana datasources"; \
	fi
	@if [ ! -f "backend/monitoring/grafana/provisioning/dashboards/dashboards.yml" ]; then \
		printf "apiVersion: 1\n\nproviders:\n  - name: 'Enterprise Dashboards'\n    orgId: 1\n    folder: ''\n    type: file\n    disableDeletion: false\n    editable: true\n    options:\n      path: /etc/grafana/dashboards\n" > backend/monitoring/grafana/provisioning/dashboards/dashboards.yml; \
		echo "✅ Created Grafana dashboard config"; \
	fi

_check-env:
	@[ -f ".env" ] || (echo "❌ .env file missing. Copy from .env.example" && exit 1)

_wait-postgres:
	@count=0; until docker exec postgres pg_isready -U airflow >/dev/null 2>&1; do \
		if [ $$count -ge 30 ]; then echo "❌ PostgreSQL timeout"; exit 1; fi; \
		count=$$((count + 1)); sleep 2; \
	done; echo "✅ PostgreSQL ready"

_install-deps-quiet:
	@docker-compose run --rm airflow_webserver bash -c '\
		pip install --no-cache-dir --quiet \
			sentry-sdk[logging] mlflow asyncpg aiohttp \
			app-store-web-scraper google-play-scraper \
			python-dotenv requests pandas numpy psycopg2-binary \
		>/dev/null 2>&1 && echo "✅ Dependencies installed" || echo "⚠️ Some dependencies failed"' 2>/dev/null

_init-airflow:
	@docker-compose run --rm airflow_webserver bash -c '\
		export PYTHONPATH="/opt/airflow:/opt/airflow/backend:$$PYTHONPATH"; \
		if airflow db check 2>&1 | grep -q "Connection is ok"; then \
			echo "✅ Airflow already initialized"; \
		else \
			echo "🚀 Initializing Airflow..."; \
			airflow db migrate >/dev/null 2>&1; \
			airflow users create --username admin --firstname Admin --lastname User \
				--role Admin --email admin@example.com --password admin >/dev/null 2>&1 || true; \
			echo "✅ Airflow initialized"; \
		fi' 2>/dev/null

_show-urls:
	@echo "🔗 Access URLs:"
	@echo "   🌐 Airflow UI:    http://localhost:8080 (admin/admin)"
	@echo "   🔧 Backend API:   http://localhost:8000"
	@echo "   🧪 MLflow:        http://localhost:5001"
	@echo "   📊 Grafana:       http://localhost:3000 (admin/admin)"
	@echo "   📈 Prometheus:    http://localhost:9090"

_backup-before-start:
	@if [ -f "data/mlflow/mlflow.db" ]; then \
		echo "💾 Creating pre-deployment backup..."; \
		$(MAKE) --no-print-directory backup >/dev/null; \
		echo "✅ Backup created"; \
	fi

_check-deployment:
	@echo "🔍 Deployment Environment Check:"
	@docker --version >/dev/null 2>&1 && echo "✅ Docker" || (echo "❌ Docker missing" && exit 1)
	@docker-compose --version >/dev/null 2>&1 && echo "✅ Docker Compose" || (echo "❌ Docker Compose missing" && exit 1)
	@[ -f ".env" ] && echo "✅ Environment file" || echo "⚠️ .env missing (will use defaults)"
	@[ -f "docker-compose.yml" ] && echo "✅ Docker Compose config" || (echo "❌ docker-compose.yml missing" && exit 1)

# ========================
# Help
# ========================

help: ## 📖 Show this help
	@echo "🚀 Enterprise Airflow Scraping System"
	@echo "====================================="
	@echo ""
	@echo "🎯 Quick Start:"
	@echo "  make up                   # Start development environment"
	@echo "  make up-prod              # Start production environment"
	@echo "  make status               # Check system health"
	@echo "  make down                 # Stop all services"
	@echo ""
	@echo "📋 Main Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -v "_" | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "💡 Examples:"
	@echo "  make up                   # Complete development setup"
	@echo "  make logs-airflow         # Debug Airflow issues"
	@echo "  make debug                # Debug DAG import problems"
	@echo "  make backup               # Backup before updates"
	@echo "  make deploy-fresh         # Deploy to new server"
	@echo ""
	@echo "🔗 After startup, access:"
	@echo "  Airflow:   http://localhost:8080 (admin/admin)"
	@echo "  Backend:   http://localhost:8000"
	@echo "  MLflow:    http://localhost:5001"
	@echo "  Grafana:   http://localhost:3000 (admin/admin)"