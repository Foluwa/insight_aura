# ========================
# Insight Aura - Unified Makefile
# Next.js Frontend + FastAPI Backend + Airflow
# ========================

.PHONY: help install up up-dev up-prod down status logs clean
.PHONY: frontend backend airflow monitoring test migrate backup deploy

# ========================
# Environment Configuration
# ========================

# Default environment variables
export HTTP_PROXY ?= 
export HTTPS_PROXY ?= 
export PROXY_ENABLED ?= false
export SENTRY_DSN ?= 
export ENVIRONMENT ?= development

# Project configuration
VENV_NAME=env_insightaura
VENV_ACTIVATE=source $(VENV_NAME)/bin/activate
PYTHON=$(VENV_NAME)/bin/python
PIP=$(VENV_NAME)/bin/pip

# ========================
# Help & Quick Start
# ========================

help: ## 📖 Show this help
	@echo "🚀 Insight Aura (Next.js + FastAPI + Airflow)"
	@echo "=============================================="
	@echo ""
	@echo "🎯 Quick Start:"
	@echo "  make quick-start          # Complete setup for new developers"
	@echo "  make up                   # Start development environment"
	@echo "  make up-prod              # Start production environment"
	@echo "  make status               # Check system health"
	@echo "  make down                 # Stop all services"
	@echo ""
	@echo "📋 Main Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -v "_" | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🔗 Access URLs (after startup):"
	@echo "  Frontend:  http://localhost (Next.js)"
	@echo "  Backend:   http://localhost/api (FastAPI)"
	@echo "  Airflow:   http://localhost/airflow (admin/admin)"
	@echo "  MLflow:    http://localhost:5001"
	@echo "  Grafana:   http://localhost/grafana (admin/admin)"

quick-start: ## 🚀 Complete setup for new developers
	@echo "🚀 Quick start for new developers"
	@echo "=================================="
	@echo "Setting up everything you need..."
	@$(MAKE) --no-print-directory install
	@$(MAKE) --no-print-directory _setup-dirs
	@$(MAKE) --no-print-directory _setup-configs
	@$(MAKE) --no-print-directory build
	@$(MAKE) --no-print-directory up-dev
	@echo ""
	@echo "🎉 Setup completed! Your development environment is ready."
	@$(MAKE) --no-print-directory _show-urls

# ========================
# Installation & Setup
# ========================

install: ## 📦 Install all dependencies (frontend + backend)
	@echo "📦 Installing all dependencies..."
	@echo "🔸 Installing backend dependencies..."
	@if [ ! -d "$(VENV_NAME)" ]; then \
		echo "Creating virtual environment..."; \
		python -m venv $(VENV_NAME); \
	fi
	@$(VENV_ACTIVATE) && pip install --upgrade pip
	@$(VENV_ACTIVATE) && pip install -r requirements.txt
	@if [ -d "frontend" ]; then \
		echo "🔸 Installing frontend dependencies..."; \
		cd frontend && npm install; \
	fi
	@echo "✅ All dependencies installed"

# ========================
# Main Service Commands
# ========================

up: up-dev ## 🚀 Start complete system (development mode)

up-dev: ## 🛠️ Start development environment with all services
	@echo "🚀 Starting Insight Aura (Development)"
	@echo "======================================"
	@$(MAKE) --no-print-directory _setup-dirs
	@$(MAKE) --no-print-directory _setup-configs
	@$(MAKE) --no-print-directory _check-env
	@echo "🔌 Starting PostgreSQL..."
	@docker-compose -f docker-compose.dev.yml up -d postgres
	@$(MAKE) --no-print-directory _wait-postgres
	@echo "📦 Installing container dependencies..."
	@$(MAKE) --no-print-directory _install-deps-quiet
	@echo "🧪 Initializing Airflow..."
	@$(MAKE) --no-print-directory _init-airflow
	@echo "🚀 Starting all development services (no nginx)..."
	@docker-compose -f docker-compose.dev.yml up -d
	@echo "⏳ Waiting for services to be ready..."
	@sleep 25
	@$(MAKE) --no-print-directory status
	@echo ""
	@echo "🎯 Development Mode - Direct Access:"
	@echo "   🎨 Frontend:      http://localhost:3000 (with hot reload)"
	@echo "   🔌 Backend API:   http://localhost:8000"
	@echo "   🌬️ Airflow UI:    http://localhost:8080"
	@echo "   📊 Grafana:       http://localhost:3001"
	@echo "   🧪 MLflow:        http://localhost:5001"

up-prod: ## 🏭 Start production environment
	@echo "🏭 Starting Insight Aura (Production)"
	@echo "====================================="
	@export ENVIRONMENT=production
	@$(MAKE) --no-print-directory _setup-dirs
	@$(MAKE) --no-print-directory _setup-configs
	@$(MAKE) --no-print-directory _backup-before-start
	@echo "🔌 Starting PostgreSQL..."
	@docker-compose -f docker-compose.prod.yml up -d postgres
	@$(MAKE) --no-print-directory _wait-postgres-prod
	@echo "📦 Installing dependencies..."
	@$(MAKE) --no-print-directory _install-deps-quiet-prod
	@echo "🧪 Initializing Airflow..."
	@$(MAKE) --no-print-directory _init-airflow-prod
	@echo "🚀 Starting production services with Caddy reverse proxy..."
	@docker-compose -f docker-compose.prod.yml up -d
	@sleep 30
	@$(MAKE) --no-print-directory status-prod
	@echo ""
	@echo "🌐 Production Mode - Caddy Reverse Proxy:"
	@echo "   🎨 Frontend:      http://localhost (Next.js production)"
	@echo "   🔌 Backend API:   http://localhost/api"
	@echo "   🌬️ Airflow UI:    http://localhost/airflow"
	@echo "   📊 Grafana:       http://localhost/grafana"
	@echo "   🧪 MLflow:        http://localhost/mlflow"

down: ## 🛑 Stop all services
	@echo "🛑 Stopping all services..."
	@if [ -f "docker-compose.dev.yml" ]; then \
		docker-compose -f docker-compose.dev.yml down; \
	fi
	@if [ -f "docker-compose.prod.yml" ]; then \
		docker-compose -f docker-compose.prod.yml down; \
	fi
	@docker-compose down 2>/dev/null || true
	@echo "✅ All services stopped"

down-clean: ## 🧹 Stop services and remove volumes
	@echo "⚠️  This will remove all containers and volumes!"
	@read -p "Continue? (y/n): " confirm; \
	if [ "$confirm" = "y" ]; then \
		docker-compose -f docker-compose.dev.yml down --volumes --remove-orphans 2>/dev/null || true; \
		docker-compose -f docker-compose.prod.yml down --volumes --remove-orphans 2>/dev/null || true; \
		docker-compose down --volumes --remove-orphans 2>/dev/null || true; \
		docker system prune -f; \
		echo "✅ Cleanup complete"; \
	else \
		echo "❌ Cancelled"; \
	fi

restart: ## 🔄 Restart all services
	@echo "🔄 Restarting all services..."
	@$(MAKE) --no-print-directory down
	@$(MAKE) --no-print-directory up
	@echo "✅ All services restarted"

# ========================
# Individual Services
# ========================

frontend: ## 🎨 Start only frontend service (development)
	@echo "🎨 Starting Frontend (Next.js) in development mode..."
	@if [ -d "frontend" ]; then \
		docker-compose -f docker-compose.dev.yml up -d frontend; \
		echo "✅ Frontend available at: http://localhost:3000"; \
	else \
		echo "❌ Frontend directory not found"; \
	fi

backend: ## ⚙️ Start only backend services (development)
	@echo "⚙️ Starting Backend services in development mode..."
	@docker-compose -f docker-compose.dev.yml up -d postgres backend
	@echo "✅ Backend available at: http://localhost:8000"

airflow: ## 🌬️ Start only Airflow (development)
	@echo "🌬️ Starting Airflow in development mode..."
	@docker-compose -f docker-compose.dev.yml up -d postgres airflow_standalone
	@echo "✅ Airflow available at: http://localhost:8080"

monitoring: ## 📊 Start only monitoring stack (development)
	@echo "📊 Starting Monitoring stack in development mode..."
	@docker-compose -f docker-compose.dev.yml up -d prometheus grafana
	@echo "✅ Monitoring available at:"
	@echo "  Grafana:    http://localhost:3001"
	@echo "  Prometheus: http://localhost:9090"

# Production service starters
frontend-prod: ## 🎨 Start frontend with caddy (production)
	@echo "🎨 Starting Frontend + Caddy (production mode)..."
	@docker-compose -f docker-compose.prod.yml up -d frontend caddy
	@echo "✅ Frontend available at: http://localhost"

backend-prod: ## ⚙️ Start backend services (production)
	@echo "⚙️ Starting Backend services (production mode)..."
	@docker-compose -f docker-compose.prod.yml up -d postgres backend
	@echo "✅ Backend available through caddy reverse proxy"

# ========================
# Development Commands
# ========================

dev-frontend: ## 🎨 Run frontend in development mode (local)
	@if [ -d "frontend" ]; then \
		echo "🎨 Starting Frontend in development mode..."; \
		cd frontend && npm run dev; \
	else \
		echo "❌ Frontend directory not found"; \
	fi

dev-backend: ## ⚙️ Run backend in development mode (local)
	@if [ ! -d "$(VENV_NAME)" ]; then \
		echo "❌ Virtual environment not found. Run 'make install' first"; \
		exit 1; \
	fi
	@echo "⚙️ Starting Backend in development mode..."
	@$(VENV_ACTIVATE) && cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-full-stack: ## 🔥 Start full development environment with hot reload
	@echo "🔥 Starting Full Stack Development Environment"
	@echo "=============================================="
	@$(MAKE) --no-print-directory _setup-dirs
	@$(MAKE) --no-print-directory _setup-configs
	@docker-compose up -d postgres
	@$(MAKE) --no-print-directory _wait-postgres
	@docker-compose up -d
	@echo "✅ Development environment ready with hot reload!"

# ========================
# Build Commands
# ========================

build: ## 🏗️ Build all Docker images
	@echo "🏗️ Building all Docker images..."
	@echo "🔸 Building development images..."
	@docker-compose -f docker-compose.dev.yml build --no-cache
	@echo "🔸 Building production images..."
	@docker-compose -f docker-compose.prod.yml build --no-cache
	@echo "✅ All images built"

build-dev: ## 🏗️ Build development images only
	@echo "🏗️ Building development images..."
	@docker-compose -f docker-compose.dev.yml build --no-cache
	@echo "✅ Development images built"

build-prod: ## 🏗️ Build production images only
	@echo "🏗️ Building production images..."
	@docker-compose -f docker-compose.prod.yml build --no-cache
	@echo "✅ Production images built"

build-frontend: ## 🏗️ Build only frontend image
	@if [ -d "frontend" ]; then \
		echo "🏗️ Building Frontend image..."; \
		docker-compose -f docker-compose.dev.yml build --no-cache frontend; \
		docker-compose -f docker-compose.prod.yml build --no-cache frontend; \
		echo "✅ Frontend image built"; \
	else \
		echo "❌ Frontend directory not found"; \
	fi

# ========================
# Testing & Quality
# ========================

test: ## 🧪 Run all tests
	@echo "🧪 Running all tests..."
	@$(MAKE) --no-print-directory test-backend
	@if [ -d "frontend" ]; then \
		$(MAKE) --no-print-directory test-frontend; \
	fi
	@echo "✅ All tests completed"

test-backend: ## 🧪 Run backend tests
	@echo "🧪 Running backend tests..."
	@if [ -d "$(VENV_NAME)" ]; then \
		$(VENV_ACTIVATE) && pytest backend/tests/ -v; \
	else \
		docker-compose exec backend python -m pytest tests/ -v; \
	fi

test-frontend: ## 🧪 Run frontend tests
	@if [ -d "frontend" ]; then \
		echo "🧪 Running frontend tests..."; \
		cd frontend && npm run test; \
	fi

# ========================
# Database Management
# ========================

migrate: ## 🗄️ Run database migrations
	@echo "🗄️ Running database migrations..."
	@if [ -d "$(VENV_NAME)" ]; then \
		$(VENV_ACTIVATE) && python backend/database/migration_runner.py; \
	else \
		docker-compose exec backend python -c "import asyncio; from backend.database.migration_runner import run_migrations; asyncio.run(run_migrations())"; \
	fi
	@echo "✅ Database migrations completed"

db-reset: ## ⚠️ Reset database (destroys data)
	@echo "⚠️ Resetting database..."
	@read -p "This will destroy all data. Continue? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker-compose down; \
		docker volume rm $$(docker volume ls -q | grep postgres) 2>/dev/null || true; \
		$(MAKE) --no-print-directory up; \
		echo "✅ Database reset completed"; \
	else \
		echo "❌ Aborted"; \
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
# Monitoring & Logs
# ========================

status: ## 📊 Check system health and show access URLs
	@echo "📊 Insight Aura System Status"
	@echo "============================="
	@echo ""
	@echo "🐳 Service Status:"
	@if docker ps --format "table {{.Names}}" | grep -q "_dev"; then \
		docker-compose -f docker-compose.dev.yml ps; \
	elif docker ps --format "table {{.Names}}" | grep -q "_prod"; then \
		docker-compose -f docker-compose.prod.yml ps; \
	else \
		docker-compose ps; \
	fi
	@echo ""
	@echo "🌐 Health Checks:"
	@if docker ps --format "table {{.Names}}" | grep -q "_dev"; then \
		printf "  %-20s " "Frontend:"; \
		if curl -s http://localhost:3000 >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi; \
		printf "  %-20s " "Backend API:"; \
		if curl -s http://localhost:8000/health >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi; \
		printf "  %-20s " "Airflow:"; \
		if curl -s http://localhost:8080/health >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi; \
		printf "  %-20s " "MLflow:"; \
		if curl -s http://localhost:5001 >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi; \
		printf "  %-20s " "Grafana:"; \
		if curl -s http://localhost:3001/api/health >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi; \
		printf "  %-20s " "PostgreSQL:"; \
		if docker exec insightaura_postgres_dev pg_isready -U airflow >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi; \
	else \
		printf "  %-20s " "Frontend:"; \
		if curl -s http://localhost >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi; \
		printf "  %-20s " "Backend API:"; \
		if curl -s http://localhost/api/health >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi; \
		printf "  %-20s " "Airflow:"; \
		if curl -s http://localhost/airflow/health >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi; \
		printf "  %-20s " "Grafana:"; \
		if curl -s http://localhost/grafana/api/health >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi; \
	fi
	@$(MAKE) --no-print-directory _show-urls

status-prod: ## 📊 Check production system health
	@echo "📊 Insight Aura Production Status"
	@echo "================================="
	@echo ""
	@echo "🐳 Service Status:"
	@docker-compose -f docker-compose.prod.yml ps
	@echo ""
	@echo "🌐 Health Checks:"
	@printf "  %-20s " "Caddy:"; \
	if curl -s http://localhost >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi
	@printf "  %-20s " "Backend API:"; \
	if curl -s http://localhost/api/health >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi
	@printf "  %-20s " "Airflow:"; \
	if curl -s http://localhost/airflow/health >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi
	@printf "  %-20s " "Grafana:"; \
	if curl -s http://localhost/grafana/api/health >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi
	@printf "  %-20s " "PostgreSQL:"; \
	if docker exec insightaura_postgres_prod pg_isready -U airflow >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Not Ready"; fi

logs: ## 📝 Show logs from all services
	@if docker ps --format "table {{.Names}}" | grep -q "_dev"; then \
		echo "📝 Development logs:"; \
		docker-compose -f docker-compose.dev.yml logs -f --tail=50; \
	elif docker ps --format "table {{.Names}}" | grep -q "_prod"; then \
		echo "📝 Production logs:"; \
		docker-compose -f docker-compose.prod.yml logs -f --tail=50; \
	else \
		echo "📝 Default logs:"; \
		docker-compose logs -f --tail=50; \
	fi

logs-frontend: ## 📝 Show frontend logs
	@if docker ps --format "table {{.Names}}" | grep -q "frontend_dev"; then \
		docker-compose -f docker-compose.dev.yml logs -f frontend; \
	elif docker ps --format "table {{.Names}}" | grep -q "frontend_prod"; then \
		docker-compose -f docker-compose.prod.yml logs -f frontend; \
	else \
		echo "❌ Frontend service not running"; \
	fi

logs-backend: ## 📝 Show backend logs
	@if docker ps --format "table {{.Names}}" | grep -q "backend_dev"; then \
		docker-compose -f docker-compose.dev.yml logs -f backend; \
	elif docker ps --format "table {{.Names}}" | grep -q "backend_prod"; then \
		docker-compose -f docker-compose.prod.yml logs -f backend; \
	else \
		echo "❌ Backend service not running"; \
	fi

logs-airflow: ## 📝 Show Airflow logs
	@if docker ps --format "table {{.Names}}" | grep -q "airflow_dev"; then \
		docker-compose -f docker-compose.dev.yml logs -f airflow_standalone; \
	elif docker ps --format "table {{.Names}}" | grep -q "airflow_prod"; then \
		docker-compose -f docker-compose.prod.yml logs -f airflow_standalone; \
	else \
		echo "❌ Airflow service not running"; \
	fi

logs-caddy: ## 📝 Show Caddy logs (production only)
	@if docker ps --format "table {{.Names}}" | grep -q "caddy_prod"; then \
		docker-compose -f docker-compose.prod.yml logs -f caddy; \
	else \
		echo "❌ Caddy only runs in production mode"; \
	fi

health: ## 🏥 Quick health check of all services
	@echo "🏥 Quick Health Check:"
	@echo "Frontend:  $$(curl -s -o /dev/null -w '%{http_code}' http://localhost || echo 'DOWN')"
	@echo "Backend:   $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health || echo 'DOWN')"
	@echo "Airflow:   $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/health || echo 'DOWN')"

# ========================
# Deployment & Production
# ========================

deploy: ## 🚀 Deploy to production
	@echo "🚀 Deploying to production..."
	@$(MAKE) --no-print-directory build
	@$(MAKE) --no-print-directory up-prod
	@echo "✅ Production deployment completed"

deploy-fresh: ## 🆕 Fresh deployment setup (new server)
	@echo "🆕 Fresh Production Deployment"
	@echo "============================="
	@$(MAKE) --no-print-directory _setup-dirs
	@$(MAKE) --no-print-directory _check-deployment
	@read -p "Environment ready. Start production deployment? (y/n): " confirm; \
	if [ "$$confirm" = "y" ]; then \
		$(MAKE) --no-print-directory deploy; \
	else \
		echo "❌ Deployment cancelled"; \
	fi

# ========================
# Caddy Management Commands
# ========================

caddy-reload: ## 🔄 Reload Caddy configuration without restart
	@if docker ps --format "table {{.Names}}" | grep -q "caddy_prod"; then \
		echo "🔄 Reloading Caddy configuration..."; \
		docker exec insightaura_caddy_prod caddy reload --config /etc/caddy/Caddyfile; \
		echo "✅ Caddy configuration reloaded"; \
	else \
		echo "❌ Caddy is not running in production mode"; \
	fi

caddy-validate: ## ✅ Validate Caddyfile configuration
	@if [ -f "caddy/Caddyfile" ]; then \
		echo "✅ Validating Caddyfile..."; \
		docker run --rm -v $(PWD)/caddy/Caddyfile:/etc/caddy/Caddyfile caddy:2-alpine caddy validate --config /etc/caddy/Caddyfile; \
	else \
		echo "❌ caddy/Caddyfile not found"; \
	fi

caddy-format: ## ✨ Format Caddyfile
	@if [ -f "caddy/Caddyfile" ]; then \
		echo "✨ Formatting Caddyfile..."; \
		docker run --rm -v $(PWD)/caddy:/etc/caddy caddy:2-alpine caddy fmt --overwrite /etc/caddy/Caddyfile; \
		echo "✅ Caddyfile formatted"; \
	else \
		echo "❌ caddy/Caddyfile not found"; \
	fi

# ========================
# Debugging & Maintenance
# ========================

shell: ## 🐚 Open Airflow container shell
	@docker-compose exec airflow_standalone bash

debug-postgres: ## 🐛 Debug PostgreSQL connection issues
	@echo "🐛 PostgreSQL Debug Information"
	@echo "=============================="
	@echo "🔍 Container Status:"
	@docker ps --filter name=postgres --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "🔍 Testing Connection:"
	@if docker ps --format "{{.Names}}" | grep -q "insightaura_postgres_dev"; then \
		echo "Development PostgreSQL:"; \
		docker exec insightaura_postgres_dev pg_isready -U airflow || echo "Connection failed"; \
		docker logs insightaura_postgres_dev --tail=10; \
	elif docker ps --format "{{.Names}}" | grep -q "insightaura_postgres_prod"; then \
		echo "Production PostgreSQL:"; \
		docker exec insightaura_postgres_prod pg_isready -U airflow || echo "Connection failed"; \
		docker logs insightaura_postgres_prod --tail=10; \
	else \
		echo "❌ No PostgreSQL container found"; \
	fi
	@echo "🐛 Debugging Airflow setup..."
	@docker-compose run --rm airflow_standalone bash -c '\
		export PYTHONPATH="/opt/airflow:/opt/airflow/backend:$$PYTHONPATH"; \
		echo "🐍 Python Path:"; python -c "import sys; [print(p) for p in sys.path]"; \
		echo ""; echo "🧪 Testing imports:"; \
		python -c "import sentry_sdk; print(\"✅ sentry_sdk\")" || echo "❌ sentry_sdk failed"; \
		python -c "import mlflow; print(\"✅ mlflow\")" || echo "❌ mlflow failed"; \
		python -c "from backend.services.app_management_service import AppManagementService; print(\"✅ backend imports\")" || echo "❌ backend imports failed"; \
		echo ""; echo "📋 DAGs:"; airflow dags list 2>&1 | head -10; \
	'

troubleshoot: ## 🔧 Show troubleshooting information
	@echo "🔧 Troubleshooting Information"
	@echo "============================="
	@echo ""
	@echo "📊 Docker System Info:"
	@docker system df
	@echo ""
	@echo "📦 Container Status:"
	@docker-compose ps
	@echo ""
	@echo "🔍 Common Issues:"
	@echo "  1. Port conflicts: Check if ports 80, 3000, 8000, 8080 are available"
	@echo "  2. Memory issues: Ensure Docker has at least 4GB RAM allocated"
	@echo "  3. Permission errors: Run 'make down-clean' and try again"
	@echo ""
	@echo "🚨 Emergency commands:"
	@echo "  make down-clean   # Stop everything and clean volumes"
	@echo "  make quick-start  # Start fresh development environment"

# ========================
# Frontend Specific Commands
# ========================

frontend-install: ## 📦 Install frontend dependencies
	@if [ -d "frontend" ]; then \
		echo "📦 Installing frontend dependencies..."; \
		cd frontend && npm install; \
		echo "✅ Frontend dependencies installed"; \
	else \
		echo "❌ Frontend directory not found"; \
	fi

frontend-build: ## 🏗️ Build frontend for production
	@if [ -d "frontend" ]; then \
		echo "🏗️ Building frontend for production..."; \
		cd frontend && npm run build; \
		echo "✅ Frontend built for production"; \
	else \
		echo "❌ Frontend directory not found"; \
	fi

frontend-lint: ## 🔍 Lint frontend code
	@if [ -d "frontend" ]; then \
		echo "🔍 Linting frontend code..."; \
		cd frontend && npm run lint; \
		echo "✅ Frontend linting completed"; \
	else \
		echo "❌ Frontend directory not found"; \
	fi

# ========================
# Internal Helper Functions
# ========================

_setup-dirs:
	@echo "📁 Creating required directories..."
	@mkdir -p data/mlflow mlflow_data/artifacts mlflow_data/models logs backups
	@mkdir -p backend/airflow/dags backend/airflow/plugins backend/airflow/logs
	@mkdir -p backend/monitoring/prometheus backend/monitoring/grafana/dashboards
	@mkdir -p backend/monitoring/grafana/provisioning/datasources
	@mkdir -p backend/monitoring/grafana/provisioning/dashboards
	@mkdir -p caddy
	@if [ -d "frontend" ]; then mkdir -p frontend/public frontend/src; fi
	@chmod -R 755 data mlflow_data logs backups backend caddy >/dev/null 2>&1 || true
	@echo "✅ All directories created"

_setup-configs:
	@echo "⚙️ Creating default configuration files..."
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env 2>/dev/null || echo "# Add your environment variables here" > .env; \
	fi
	@if [ -d "frontend" ] && [ ! -f "frontend/.env.local" ]; then \
		echo "Creating frontend/.env.local..."; \
		echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > frontend/.env.local; \
		echo "NEXT_PUBLIC_APP_ENV=development" >> frontend/.env.local; \
	fi
	@if [ ! -f "caddy/Caddyfile" ]; then \
		echo "Creating default Caddyfile..."; \
		printf "localhost {\n  reverse_proxy /api/* backend:8000\n  reverse_proxy /airflow/* airflow_standalone:8080\n  reverse_proxy /grafana/* grafana:3000\n  reverse_proxy /mlflow/* mlflow:5001\n  reverse_proxy frontend:3000\n}\n" > caddy/Caddyfile; \
	fi
	@$(MAKE) --no-print-directory _create-monitoring-configs
	@echo "✅ Configuration files ready"

_create-monitoring-configs:
	@if [ ! -f "backend/monitoring/prometheus/prometheus.yml" ]; then \
		printf "global:\n  scrape_interval: 15s\nscrape_configs:\n  - job_name: 'prometheus'\n    static_configs:\n      - targets: ['localhost:9090']\n  - job_name: 'airflow'\n    static_configs:\n      - targets: ['airflow_standalone:8080']\n    metrics_path: '/admin/metrics'\n  - job_name: 'backend'\n    static_configs:\n      - targets: ['backend:8000']\n    metrics_path: '/metrics'\n" > backend/monitoring/prometheus/prometheus.yml; \
	fi
	@if [ ! -f "backend/monitoring/grafana/grafana.ini" ]; then \
		printf "[security]\nadmin_user = admin\nadmin_password = admin\n[server]\nhttp_port = 3000\n" > backend/monitoring/grafana/grafana.ini; \
	fi

_check-env:
	@[ -f ".env" ] || (echo "❌ .env file missing. Copy from .env.example" && exit 1)

_wait-postgres:
	@count=0; until docker exec insightaura_postgres_dev pg_isready -U airflow >/dev/null 2>&1; do \
		if [ $$count -ge 30 ]; then echo "❌ PostgreSQL timeout"; exit 1; fi; \
		count=$$(( count + 1 )); sleep 2; \
	done; echo "✅ PostgreSQL ready"

_wait-postgres-prod:
	@count=0; until docker exec insightaura_postgres_prod pg_isready -U airflow >/dev/null 2>&1; do \
		if [ $$count -ge 30 ]; then echo "❌ PostgreSQL timeout"; exit 1; fi; \
		count=$$(( count + 1 )); sleep 2; \
	done; echo "✅ PostgreSQL ready"

_install-deps-quiet:
	@docker-compose -f docker-compose.dev.yml run --rm airflow_standalone bash -c '\
		pip install --no-cache-dir --quiet \
			sentry-sdk[logging] mlflow asyncpg aiohttp \
			app-store-web-scraper google-play-scraper \
			python-dotenv requests pandas numpy psycopg2-binary \
		>/dev/null 2>&1 && echo "✅ Dependencies installed" || echo "⚠️ Some dependencies failed"' 2>/dev/null

_install-deps-quiet-prod:
	@docker-compose -f docker-compose.prod.yml run --rm airflow_standalone bash -c '\
		pip install --no-cache-dir --quiet \
			sentry-sdk[logging] mlflow asyncpg aiohttp \
			app-store-web-scraper google-play-scraper \
			python-dotenv requests pandas numpy psycopg2-binary \
		>/dev/null 2>&1 && echo "✅ Dependencies installed" || echo "⚠️ Some dependencies failed"' 2>/dev/null

_init-airflow:
	@docker-compose -f docker-compose.dev.yml run --rm airflow_standalone bash -c '\
		export PYTHONPATH="/opt/airflow:/opt/airflow/backend:$PYTHONPATH"; \
		if airflow db check 2>&1 | grep -q "Connection is ok"; then \
			echo "✅ Airflow already initialized"; \
		else \
			echo "🚀 Initializing Airflow..."; \
			airflow db migrate >/dev/null 2>&1; \
			airflow users create --username admin --firstname Admin --lastname User \
				--role Admin --email admin@example.com --password admin >/dev/null 2>&1 || true; \
			echo "✅ Airflow initialized"; \
		fi' 2>/dev/null

_init-airflow-prod:
	@docker-compose -f docker-compose.prod.yml run --rm airflow_standalone bash -c '\
		export PYTHONPATH="/opt/airflow:/opt/airflow/backend:$PYTHONPATH"; \
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
	@echo ""
	@echo "🔗 Access URLs:"
	@if docker ps --format "table {{.Names}}" | grep -q "_dev"; then \
		echo "   🎯 Development Mode:"; \
		echo "   🎨 Frontend:      http://localhost:3000 (Next.js with hot reload)"; \
		echo "   🔌 Backend API:   http://localhost:8000"; \
		echo "   🌬️ Airflow UI:    http://localhost:8080 (admin/admin)"; \
		echo "   🧪 MLflow:        http://localhost:5001"; \
		echo "   📊 Grafana:       http://localhost:3001 (admin/admin)"; \
		echo "   📈 Prometheus:    http://localhost:9090"; \
	else \
		echo "   🌐 Production Mode (via Caddy):"; \
		echo "   🎨 Frontend:      http://localhost (Next.js production)"; \
		echo "   🔌 Backend API:   http://localhost/api"; \
		echo "   🌬️ Airflow UI:    http://localhost/airflow (admin/admin)"; \
		echo "   📊 Grafana:       http://localhost/grafana (admin/admin)"; \
		echo "   🧪 MLflow:        http://localhost/mlflow"; \
		echo "   🔧 Caddy Health:  http://localhost/health"; \
	fi
	@echo ""
	@echo "📚 Next steps:"
	@if [ -d "frontend" ]; then echo "  1. Edit frontend/src/app/page.tsx to customize the homepage"; fi
	@echo "  2. Check backend/api/routes/ for API endpoints"
	@echo "  3. View logs with: make logs"
	@echo "  4. Stop services with: make down"

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