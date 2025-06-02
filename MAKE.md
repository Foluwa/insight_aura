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
