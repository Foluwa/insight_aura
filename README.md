
# 📱 Sentiment Analysis Platform

A fullstack platform to scrape app reviews from Google Play and Apple App Store, perform sentiment analysis using fine-tuned BERT models, compare applications, track model performance, and monitor infrastructure — scalable and production-ready.

---

allows users to search for apps, analyze sentiment (positive, negative, neutral), compare reviews between platforms, and share results via unique links.


## Usage

1. **Search Apps**: Enter an app name and select Google Play Store or Apple App Store.
2. **Sentiment Analysis**: Reviews are analyzed and classified as positive, negative, or neutral.
3. **Comparison**: Compare reviews between platforms and share analysis results via unique links.
4. **Notifications**: Stay updated when reviews are fetched or new data is available.

---

### Scraping
- Multithreaded scrapers ensure backend performance is non-blocking.
- Use rotating proxies to prevent IP bans.

### Sentiment Analysis
- The platform uses BERT for sentiment classification, which can be fine-tuned further.

### Database
- Optimized schema with indexes for app IDs and deduplication.
- Scales efficiently with high query volume.



## 📚 Project Structure

```plaintext
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── lifespan.py 
│   │   ├── routes/
│   │   │   ├── scraper.py
│   │   │   ├── sentiment.py
│   │   │   ├── comparison.py
│   │   └── utils/
│   │       ├── notification.py
│   │       ├── threading.py
│   ├── models/
│   │   └── sentiment_bert/                 # Fine-tuned BERT models
│   ├── schemas/
│   │   ├── app_schema.py
│   │   ├── review_schema.py
│   ├── services/
│   │   ├── base_service.py    
│   │   ├── review_service.py    
│   │   ├── google_review_scraper.py
│   │   ├── apple_review_scraper.py
│   ├── tests/
│   │   ├── services/
│   │   │   ├── test_review_service.py
│   ├── database/
│   │   ├── connection.py                    # Connect to external PostgreSQL
│   │   ├── queries.py
│   │   ├── migration_runner.py              # Manual class-based migration runner
│   │   └── migrations/
│   │       ├── __init__.py
│   │       ├── base_migration.py
│   │       ├── 001_create_apps_table.py
│   │       ├── 002_create_reviews_table.py
│   │       ├── 003_create_search_history_table.py
│   ├── airflow/
│   │   ├── dags/
│   │   │   ├── scrape_reviews_dag.py
│   │   │   ├── retrain_model_dag.py
│   │   ├── plugins/
│   │   │   └── telegram_alert.py
│   ├── mlflow_server/
│   │   └── config/
│   │       └── mlflow.cfg
│   ├── monitoring/
│   │   ├── grafana/
│   │   │   ├── grafana.ini
│   │   │   └── dashboards/
│   │   │       ├── system_metrics.json
│   │   │       ├── scraping_metrics.json
│   │   ├── prometheus/
│   │   │   └── prometheus.yml
│   ├── docker/
│   │   ├── Dockerfile.backend
│   │   ├── Dockerfile.airflow
│   │   ├── Dockerfile.mlflow
│   │   ├── Dockerfile.prometheus
│   │   ├── Dockerfile.grafana
│   ├── cron.py                              
│   ├── main.py                              # FastAPI application entry
├── frontend/
│   ├── components/
│   │   ├── SearchBar.jsx
│   │   ├── AppComparison.jsx
│   ├── pages/
│   │   ├── index.js
│   │   ├── compare/[id].js
│   ├── redux/
│   │   ├── store.js
│   │   ├── slices/
│   │   │   ├── appSlice.js
│   ├── utils/
│   │   └── api.js
│   ├── Dockerfile.frontend
├── datasets/
│   ├── raw/
│   │   ├── initial_reviews_google.csv
│   │   ├── initial_reviews_apple.csv
│   ├── processed/
│   │   ├── labeled_reviews.csv
│   ├── README.md                            
├── notebooks/
│   ├── sentiment_experiment.ipynb            
│   ├── scraper_experiment.ipynb              
├── infrastructure/
│   ├── airflow/
│   │   └── airflow.cfg
│   ├── grafana/
│   │   ├── grafana.ini
│   │   └── dashboards/
│   │       ├── system_metrics.json
│   │       ├── scraping_metrics.json
│   ├── mlflow/
│   │   └── mlflow.cfg
│   ├── deployment/
│   │   ├── docker-compose.prod.yml          # Production Swarm Compose
│   │   ├── traefik.yml                      # Traefik reverse proxy config
├── .env.development                         # Development environment variables
├── .env.production                          # Production environment variables
├── docker-compose.yml                       # Local dev docker-compose
├── Makefile                                 # Automation commands
├── README.md                                # Project Documentation


- `backend/`: FastAPI app, scrapers, BERT fine-tuning, business logic
- `frontend/`: Next.js (with Redux Toolkit) web frontend
- `datasets/`: Initial datasets (raw, processed)
- `notebooks/`: Experimental Jupyter notebooks
- `infrastructure/`: Configurations and deployments (Airflow, Grafana, MLflow, Traefik)
- `.env.*`: Environment-specific variables
- `docker-compose.yml`: Development stack definition
- `README.md`: Documentation
```

---

## 🛠 Technology Stack

| Layer | Technology |
|:------|:-----------|
| Frontend | Next.js, Redux Toolkit |
| Backend | FastAPI, Starlette, Pydantic |
| Scraping | Airflow Orchestration |
| ML Models | BERT fine-tuning, HuggingFace, MLflow |
| Database | External PostgreSQL (cloud-managed or separate server) |
| Monitoring | Prometheus + Grafana |
| Infrastructure | Docker Swarm, Traefik, Spot VMs (GCP) |
| Notifications | Email Alerts + Telegram API |

---

## 📦 Environment Management

The system uses **different `.env` files** for development and production:

| Environment | File | Purpose |
|:------------|:-----|:--------|
| Development | `.env.development` | Connects to local or test database |
| Production  | `.env.production`  | Connects to cloud-hosted or external database |

**Before running** docker-compose or make commands, set the correct environment:

- For **development**:
  ```bash
  make set_env_dev
  make up
  ```

- For **production**:
  ```bash
  make set_env_prod
  docker stack deploy -c infrastructure/deployment/docker-compose.prod.yml your_stack_name
  ```

> **Note**: `backend` connects to database via `DATABASE_URL` environment variable only.

---

## 🛠 Using the Makefile

The Makefile automates all essential tasks:

| Command | Description |
|:--------|:------------|
| `make build` | Build all backend docker images |
| `make start_backend` | Start the FastAPI backend service |
| `make start_monitoring` | Start Grafana and Prometheus |
| `make start_airflow` | Start Airflow scheduler, webserver, worker |
| `make migrate` | Run manual class-based database migrations |
| `make up` | Bring up all services |
| `make down` | Bring down all services |
| `make logs` | View service logs |
| `make clean` | Clean up containers and volumes |
| `make restart` | Restart all services |
| `make build_and_up` | Build images and start services |
| `make set_env_dev` | Copy `.env.development` to `.env` |
| `make set_env_prod` | Copy `.env.production` to `.env` |

---


## 🛠️ Development Workflow with Makefile

This project uses a **Makefile** to simplify common tasks.

### Available Commands:

| Command | Description |
|:-------:|:-----------:|
| `make install` | Install Python dependencies into the virtual environment |
| `make migrate` | Run database migrations |
| `make backend-dev` | Start the FastAPI backend server (with Hot Reload) |
| `make docker-build` | Build Docker images |
| `make docker-up` | Start all Docker containers (backend, airflow, mlflow, etc.) |
| `make docker-down` | Stop all Docker containers |
| `make docker-restart` | Restart Docker containers cleanly |
| `make test` | Run backend unit tests |

---



## 🛠️ Makefile Commands Reference

### ⚙️ Setup & Install

| Command | Description |
|--------|-------------|
| `make install` | Install Python dependencies using `pip` in the virtualenv |
| `make check-env` | Ensure `.env` file exists |
| `make check-venv` | Ensure Python virtualenv exists |
| `make load-env` | Export all variables from `.env` into the shell |

### 🚀 Application Startup

| Command | Description |
|--------|-------------|
| `make up` | Smart startup: starts Postgres, waits, initializes Airflow if needed, then starts everything |
| `make backend-dev` | Run FastAPI dev server (`uvicorn`) |
| `make bootstrap-airflow` | Init Airflow DB if needed and restart services |

### 🐳 Docker Infrastructure

| Command | Description |
|--------|-------------|
| `make docker-up` | Start all Docker containers |
| `make docker-down` | Stop all containers |
| `make docker-restart` | Restart all containers |
| `make docker-build` | Rebuild all Docker images |
| `make docker-status` | Show Docker container statuses |
| `make docker-logs` | Show container logs |
| `make docker-prune` | Remove unused Docker resources |

### 🔁 Database

| Command | Description |
|--------|-------------|
| `make migrate` | Run database migrations |
| `make backup-db` | Backup PostgreSQL to timestamped `.sql` |

### 🌬️ Airflow

| Command | Description |
|--------|-------------|
| `make airflow-init` | Initialize Airflow DB |
| `make airflow-version` | Show Airflow version |
| `make health-check` | Ping services: FastAPI, Airflow, Postgres |

### ⚠️ Dev-Only

| Command | Description |
|--------|-------------|
| `make kill-all` | ⚠️ Wipe all Docker volumes + containers (with prompt) |



### 🧩 Setup

```bash
# 1. Clone the repo
git clone https://github.com/your-username/sentiment-analysis-platform.git
cd sentiment-analysis-platform

# 2. Create a virtual environment manually if it doesn't exist
python3 -m venv env_sent

# 3. Activate your virtual environment
source env_sent/bin/activate

# 4. Install all Python dependencies
make install

# 5. Create a .env file (copy from .env.example if available)
cp .env.example .env

# 6. Run database migrations
make migrate

# 7. Start backend server for development
make backend-dev
```


## 🧠 Features

- **App Review Scraping** from Google Play Store and Apple App Store
- **Sentiment Analysis** (Positive, Neutral, Negative) using fine-tuned BERT models
- **App Comparison** between platforms
- **Scheduled Retraining** via Airflow DAGs
- **Scraper Orchestration** using Airflow
- **Model Tracking** using MLflow
- **Monitoring and Alerting** with Prometheus, Grafana, Email, Telegram
- **Dockerized Services**, **Swarm Deployment** ready
- **External PostgreSQL Database** for persistence and scaling

---

## 🗄 Datasets

Initial data is stored inside:

```plaintext
datasets/
├── raw/
│   ├── initial_reviews_google.csv
│   ├── initial_reviews_apple.csv
├── processed/
│   ├── labeled_reviews.csv
```

- `raw/`: Raw scraped data (unlabeled)
- `processed/`: Auto-labeled or human-labeled sentiment data for model fine-tuning

---

## 🚨 Important Notes

- **Database**: No internal Postgres container is provided. Use a separate managed PostgreSQL server.
- **Production Readiness**: Use GCP Spot VMs for heavy model training; Hetzner CPU server for inference.
- **Security**: Set strong `.env` secrets for production.
- **Scaling**: Ready for Docker Swarm clustering and Traefik load balancing.

---

## 🚀 Quick Start (Local Development)

```bash
# Setup local env
make set_env_dev

# Build images
make build

# Run services
make up

# Access services
- Backend API: http://localhost:8000
- Airflow Web UI: http://localhost:8080
- Grafana Dashboards: http://localhost:3000
- MLflow Tracking: http://localhost:5000
```

---

## 📜 License

MIT License - Feel free to use, modify, and contribute.

---
