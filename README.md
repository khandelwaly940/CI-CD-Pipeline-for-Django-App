## 📌 Project Overview

At a high level, this project is a Django-based web application backed by PostgreSQL. The entire infrastructure is containerized using Docker, making it completely environment-agnostic. Moreover, I've built out a complete Continuous Integration and Continuous Deployment (CI/CD) pipeline using GitHub Actions to automatically lint, test, and deploy the application to Heroku.

## System Architecture & Workflow

Understanding the underlying architecture is critical for both development and operations. Here's a breakdown of how the components fit together:

### 1. The Application Layer (Django + Gunicorn)

The core application is built with Django, serving as the backend framework. In a production environment, simply running `python manage.py runserver` is insecure and inefficient. Instead, we use **Gunicorn** as our highly reliable WSGI HTTP Server.

Static files (CSS, JS, images) are served by **WhiteNoise**, which integrates directly into Django’s middleware hierarchy. This allows the application to serve its own static assets without needing a separate Nginx or Apache reverse proxy, simplifying the deployment footprint.

### 2. The Data Layer (PostgreSQL)

We moved away from Django's default SQLite (which isn't suited for concurrent writes) to PostgreSQL. In our local development (`docker-compose.yml`), we spin up a dedicated `postgres:15` container. The application dynamically hooks into this database through connection strings defined via environment variables (`django-environ`), meaning our code never hardcodes sensitive database credentials.

### 3. Containerization Strategy (Docker)

The application relies on a Docker-first workflow.

- The `Dockerfile` is based on `python:3.10-slim` to keep the image lightweight.
- We utilize a custom `entrypoint.sh` script. When the container starts, this script automatically applies any pending database migrations (`python manage.py migrate`) and collects static files (`collectstatic`) before handing off execution to Gunicorn. This guarantees that whenever a new container spins up, its database schema is instantly in sync with the codebase.

### 4. Continuous Integration / Continuous Deployment (GitHub Actions & Heroku)

The CI/CD pipeline (`.github/workflows/main.yml`) is split into two primary jobs:

- **The `test` Job**: Triggered on every pull request and push to the `main` branch. It acts as our first line of defense.
  1. It spins up a temporary PostgreSQL service container.
  2. Installs requirements.
  3. Validates code formatting and layout using `Black` and `Flake8`.
  4. Executes unit tests via `PyTest`. If any of these steps fail, the pipeline halts—protecting the main branch from broken code.

- **The `deploy` Job**: Runs strictly when code is merged or pushed directly to the `main` branch, _only if_ the `test` job succeeds. It securely connects to Heroku via API keys managed in GitHub Secrets and pushes the Docker container to the Heroku container registry, releasing the new version into production.

## Local Development Setup (Quick Start)

The developer experience is optimized around Docker Compose. You do not need to install Python, pip, or PostgreSQL locally on your host machine.

### Prerequisites

- Docker Engine & Docker Compose

### Running the Project

1. **Clone the repository** and navigate to the project root (`CICD/`).
2. **Setup environment variables**:
   ```bash
   cp .env.example .env
   ```
   _(The template provides safe defaults for local development setup)_
3. **Build and start the services**:
   ```bash
   docker-compose up --build
   ```
   Docker will build the web image, pull PostgreSQL, run migrations automatically, and start the development server.
4. **Access the application**: Navigate to `http://localhost:8000`.

### Running Tests and Linting Locally

You can run the exact same checks the CI pipeline uses straight from your local containers.

- **Run PyTest**:
  ```bash
  docker-compose run --rm web pytest
  ```
- **Check formatting with Black**:
  ```bash
  docker-compose run --rm web black --check .
  ```
- **Run Flake8 Linter**:
  ```bash
  docker-compose run --rm web flake8 .
  ```

If `black` complains about formatting, you can automatically fix it by running:

```bash
docker-compose run --rm web black .
```

## Design Decisions

**Why Docker?**
It eliminates the "it works on my machine" problem. Testing becomes deterministic since GitHub Actions builds the same image we run locally, ensuring total parity between development and production.

**Why Black and Flake8?**
`Black` enforces a strict, uncompromising code style, stopping debates in code reviews about formatting. `Flake8` complements it by catching logical or syntactical errors (like unused imports or undefined variables) before they even hit execution.

**Why decouple configuration from code (`django-environ`)?**
This adheres to the [Twelve-Factor App methodology](https://12factor.net/config) for configuration. By moving `SECRET_KEY`, `DEBUG`, and database URIs into the environment, we can deploy the exact same codebase to Staging, UAT, and Production just by swapping out the environment variables in Heroku or our local `.env` file.
