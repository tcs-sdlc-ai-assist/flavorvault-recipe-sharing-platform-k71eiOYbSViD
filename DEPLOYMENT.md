# FlavorVault Deployment Guide

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Environment Variables](#environment-variables)
- [Database Provisioning](#database-provisioning)
- [Database Migrations](#database-migrations)
- [Seed Data](#seed-data)
- [Vercel Deployment](#vercel-deployment)
- [Docker Deployment](#docker-deployment)
- [CI/CD Pipeline](#cicd-pipeline)
- [Monitoring and Logging](#monitoring-and-logging)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 15+ (local or managed)
- Git
- Vercel CLI (optional, for Vercel deployments)
- Docker and Docker Compose (optional, for containerized deployments)

---

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/flavorvault.git
cd flavorvault
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your local configuration (see Environment Variables section below)
```

### 5. Run Database Migrations

```bash
alembic upgrade head
```

### 6. Seed the Database (Optional)

```bash
python -m app.scripts.seed
```

### 7. Start the Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

---

## Environment Variables

Create a `.env` file in the project root with the following variables:

### Required Variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string (async driver) | `postgresql+asyncpg://user:pass@host:5432/flavorvault` |
| `SECRET_KEY` | Secret key for JWT token signing (min 32 chars) | `your-super-secret-key-at-least-32-characters` |

### Optional Variables

| Variable | Description | Default |
|---|---|---|
| `ENVIRONMENT` | Deployment environment | `development` |
| `DEBUG` | Enable debug mode | `false` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:3000` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token TTL in minutes | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | JWT refresh token TTL in days | `7` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DATABASE_POOL_SIZE` | SQLAlchemy connection pool size | `5` |
| `DATABASE_MAX_OVERFLOW` | SQLAlchemy max overflow connections | `10` |
| `CHROMA_DB_PATH` | Path for ChromaDB persistent storage | `./chroma_data` |
| `OPENAI_API_KEY` | OpenAI API key for embeddings (if using RAG) | _(none)_ |

### Example `.env` File

```env
# Database
DATABASE_URL=postgresql+asyncpg://flavorvault:password@localhost:5432/flavorvault

# Security
SECRET_KEY=change-this-to-a-random-string-at-least-32-characters-long
ENVIRONMENT=development
DEBUG=true

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Logging
LOG_LEVEL=DEBUG

# Database Pool
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Vector DB (optional)
CHROMA_DB_PATH=./chroma_data
```

### Important Notes on Environment Variables

- **`SECRET_KEY`**: Generate a strong random key for production. Use `python -c "import secrets; print(secrets.token_urlsafe(64))"` to generate one.
- **`DATABASE_URL`**: Must use the `postgresql+asyncpg://` scheme for async SQLAlchemy. If your provider gives you a `postgres://` URL, replace the scheme accordingly.
- **`ALLOWED_ORIGINS`**: In production, set this to your actual frontend domain(s). Never use `*` in production.

---

## Database Provisioning

### Option 1: Managed PostgreSQL (Recommended for Production)

#### Neon (Recommended for Vercel)

1. Sign up at [neon.tech](https://neon.tech)
2. Create a new project named `flavorvault`
3. Copy the connection string from the dashboard
4. Replace the scheme: change `postgres://` to `postgresql+asyncpg://`
5. Set the modified URL as `DATABASE_URL` in your environment

```bash
# Neon provides a URL like:
# postgres://user:pass@ep-cool-name-123456.us-east-2.aws.neon.tech/flavorvault?sslmode=require

# Convert to async format:
# postgresql+asyncpg://user:pass@ep-cool-name-123456.us-east-2.aws.neon.tech/flavorvault?ssl=require
```

> **Note**: For asyncpg, use `ssl=require` instead of `sslmode=require`.

#### Supabase

1. Sign up at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to Settings → Database → Connection string
4. Select "URI" and copy the connection string
5. Replace `postgres://` with `postgresql+asyncpg://`
6. Replace `sslmode=require` with `ssl=require`

#### AWS RDS

1. Create a PostgreSQL RDS instance (db.t3.micro for development)
2. Configure the security group to allow inbound traffic on port 5432
3. Use the endpoint, username, and password to construct the connection string:
   ```
   postgresql+asyncpg://username:password@your-rds-endpoint.region.rds.amazonaws.com:5432/flavorvault
   ```

### Option 2: Local PostgreSQL (Development)

```bash
# Using Docker
docker run -d \
  --name flavorvault-db \
  -e POSTGRES_USER=flavorvault \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=flavorvault \
  -p 5432:5432 \
  postgres:15-alpine

# Connection string:
# postgresql+asyncpg://flavorvault:password@localhost:5432/flavorvault
```

### Option 3: SQLite (Quick Local Testing Only)

For quick local testing, you can use SQLite with aiosqlite:

```env
DATABASE_URL=sqlite+aiosqlite:///./flavorvault.db
```

> **Warning**: SQLite is not recommended for production. Some features (e.g., array columns, advanced JSON queries) may not work with SQLite.

---

## Database Migrations

FlavorVault uses Alembic for database schema migrations.

### Initial Setup (Already Done)

```bash
# Initialize Alembic (only needed once, already configured in this project)
alembic init alembic
```

### Running Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply migrations up to a specific revision
alembic upgrade <revision_id>

# Rollback the last migration
alembic downgrade -1

# Rollback all migrations
alembic downgrade base

# View current migration status
alembic current

# View migration history
alembic history --verbose
```

### Creating New Migrations

```bash
# Auto-generate a migration from model changes
alembic revision --autogenerate -m "add_recipe_tags_table"

# Create an empty migration for manual SQL
alembic revision -m "add_custom_index"
```

### Migration Best Practices

1. **Always review auto-generated migrations** before applying them. Alembic may miss certain changes (e.g., renaming columns vs. dropping and recreating).
2. **Test migrations on a staging database** before applying to production.
3. **Never edit a migration that has already been applied** to a shared database. Create a new migration instead.
4. **Include both `upgrade()` and `downgrade()`** functions in every migration for rollback capability.
5. **Run migrations as part of your deployment pipeline**, not manually in production.

### Running Migrations in Production

```bash
# Set the production DATABASE_URL
export DATABASE_URL="postgresql+asyncpg://user:pass@prod-host:5432/flavorvault"

# Run migrations
alembic upgrade head
```

> **Note**: For Alembic migrations, you may need a synchronous database URL. If your `alembic/env.py` is configured for async, use the asyncpg URL. Otherwise, replace `asyncpg` with `psycopg2` for the migration runner:
> ```
> postgresql+psycopg2://user:pass@host:5432/flavorvault
> ```

---

## Seed Data

### Running the Seed Script

```bash
# Seed the database with initial data (admin user, sample recipes, categories, etc.)
python -m app.scripts.seed
```

### What Gets Seeded

- **Admin user**: `admin@flavorvault.com` / `admin123` (change password immediately in production)
- **Default categories**: Common recipe categories (Appetizers, Main Courses, Desserts, etc.)
- **Sample recipes**: A few example recipes for demonstration purposes
- **Tags**: Common cooking tags (Vegetarian, Vegan, Gluten-Free, Quick, etc.)

### Custom Seed Data

To add custom seed data, edit `app/scripts/seed.py` and add your entries to the appropriate seed functions.

### Resetting the Database

```bash
# Drop all tables and re-run migrations
alembic downgrade base
alembic upgrade head

# Re-seed
python -m app.scripts.seed
```

---

## Vercel Deployment

### Prerequisites

- Vercel account ([vercel.com](https://vercel.com))
- Vercel CLI installed: `npm i -g vercel`
- A managed PostgreSQL database (Neon recommended for Vercel)

### Step 1: Configure `vercel.json`

Create or verify `vercel.json` in the project root:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ]
}
```

### Step 2: Set Environment Variables on Vercel

```bash
# Using Vercel CLI
vercel env add DATABASE_URL production
vercel env add SECRET_KEY production
vercel env add ENVIRONMENT production
vercel env add ALLOWED_ORIGINS production

# Or set them in the Vercel Dashboard:
# Project Settings → Environment Variables
```

Required environment variables for Vercel:

| Variable | Value |
|---|---|
| `DATABASE_URL` | Your managed PostgreSQL async connection string |
| `SECRET_KEY` | A strong random secret key |
| `ENVIRONMENT` | `production` |
| `ALLOWED_ORIGINS` | Your frontend domain(s) |
| `LOG_LEVEL` | `WARNING` or `INFO` |

### Step 3: Deploy

```bash
# Link to Vercel project (first time)
vercel link

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

### Step 4: Run Migrations on Production Database

Vercel serverless functions cannot run long-lived migration processes. Run migrations from your local machine or CI/CD pipeline against the production database:

```bash
# Point to production database
export DATABASE_URL="postgresql+asyncpg://user:pass@prod-host:5432/flavorvault"

# Run migrations
alembic upgrade head
```

### Vercel-Specific Considerations

- **Cold starts**: Serverless functions have cold start latency. The first request after inactivity may be slower.
- **Execution timeout**: Vercel Hobby plan has a 10-second timeout; Pro plan has 60 seconds. Optimize slow queries accordingly.
- **No persistent filesystem**: Do not rely on local file storage. Use cloud storage (S3, Cloudflare R2) for uploaded files.
- **No background tasks**: Vercel functions terminate after the response is sent. Use external task queues (e.g., Vercel Cron, external workers) for background processing.
- **ChromaDB**: PersistentClient will NOT work on Vercel (no writable filesystem). Use ChromaDB Cloud or an alternative vector database for production RAG features.

---

## Docker Deployment

### Using Docker Compose (Recommended)

Create a `docker-compose.yml`:

```yaml
version: "3.9"

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://flavorvault:password@db:5432/flavorvault
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-http://localhost:3000}
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=flavorvault
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=flavorvault
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U flavorvault"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
```

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run migrations and start the server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

### Build and Run

```bash
# Build and start all services
docker compose up -d --build

# View logs
docker compose logs -f app

# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes database data)
docker compose down -v
```

---

## CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/ci.yml`:

```yaml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: flavorvault_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run linting
        run: |
          pip install ruff
          ruff check app/

      - name: Run migrations
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/flavorvault_test
          SECRET_KEY: test-secret-key-for-ci-at-least-32-chars
        run: alembic upgrade head

      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/flavorvault_test
          SECRET_KEY: test-secret-key-for-ci-at-least-32-chars
          ENVIRONMENT: testing
        run: pytest -v --tb=short

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: "--prod"
```

### Required GitHub Secrets

| Secret | Description |
|---|---|
| `VERCEL_TOKEN` | Vercel personal access token |
| `VERCEL_ORG_ID` | Vercel organization/team ID |
| `VERCEL_PROJECT_ID` | Vercel project ID |

### CI/CD Best Practices

1. **Run tests on every PR** before merging to main.
2. **Run migrations in CI** to catch schema issues early.
3. **Deploy only from main branch** after tests pass.
4. **Use staging environments** for pre-production validation.
5. **Pin dependency versions** in `requirements.txt` for reproducible builds.

---

## Monitoring and Logging

### Structured Logging

FlavorVault uses Python's built-in `logging` module with structured log messages. Configure the log level via the `LOG_LEVEL` environment variable.

```python
# Logs are written to stdout in a structured format
# Set LOG_LEVEL=DEBUG for verbose output during development
# Set LOG_LEVEL=WARNING or LOG_LEVEL=ERROR for production
```

### Health Check Endpoint

The application exposes a health check endpoint:

```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

Use this endpoint for:
- Load balancer health checks
- Uptime monitoring (e.g., UptimeRobot, Pingdom)
- Kubernetes liveness/readiness probes

### Recommended Monitoring Tools

- **Sentry**: Error tracking and performance monitoring. Add `sentry-sdk[fastapi]` to requirements and configure the DSN.
- **Datadog / New Relic**: Full APM with request tracing.
- **Prometheus + Grafana**: Metrics collection and dashboarding (use `prometheus-fastapi-instrumentator`).

---

## Troubleshooting

### Common Issues

#### 1. `ModuleNotFoundError: No module named 'app'`

**Cause**: Python cannot find the `app` package.

**Fix**: Ensure you are running commands from the project root directory, and that `app/__init__.py` exists.

```bash
# Run from project root
cd /path/to/flavorvault
uvicorn app.main:app --reload
```

#### 2. `sqlalchemy.exc.OperationalError: could not connect to server`

**Cause**: Database is not running or connection string is incorrect.

**Fix**:
- Verify PostgreSQL is running: `pg_isready -h localhost -p 5432`
- Check `DATABASE_URL` in `.env` for typos
- Ensure the database exists: `createdb flavorvault`
- For Docker: ensure the database container is healthy: `docker compose ps`

#### 3. `MissingGreenlet: greenlet_spawn has not been called`

**Cause**: Lazy loading a SQLAlchemy relationship inside an async context.

**Fix**: Ensure all `relationship()` declarations use `lazy="selectin"`, and use `selectinload()` in queries that access nested relationships.

#### 4. `pydantic_core._pydantic_core.ValidationError: Extra inputs are not permitted`

**Cause**: Pydantic Settings receiving unexpected environment variables (common on Vercel/Docker).

**Fix**: Ensure your Settings class includes `extra="ignore"`:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

#### 5. `alembic.util.exc.CommandError: Can't locate revision identified by 'xxx'`

**Cause**: Migration history is out of sync with the database.

**Fix**:
```bash
# Check current state
alembic current

# If the database is empty, stamp it at base and re-run
alembic stamp base
alembic upgrade head
```

#### 6. `ImportError: email-validator is not installed`

**Cause**: A Pydantic schema uses `EmailStr` but `email-validator` is not installed.

**Fix**: Ensure `email-validator` is in `requirements.txt` and installed:
```bash
pip install email-validator
```

#### 7. `asyncpg.exceptions.InvalidCatalogNameError: database "flavorvault" does not exist`

**Cause**: The target database has not been created.

**Fix**:
```bash
# Connect to PostgreSQL and create the database
psql -U postgres -c "CREATE DATABASE flavorvault;"
```

#### 8. Vercel deployment returns 500 Internal Server Error

**Cause**: Usually a missing environment variable or failed import.

**Fix**:
1. Check Vercel function logs: `vercel logs <deployment-url>`
2. Verify all required environment variables are set in Vercel dashboard
3. Ensure `requirements.txt` includes all dependencies
4. Test locally with `ENVIRONMENT=production` to reproduce

#### 9. CORS errors in the browser

**Cause**: Frontend origin is not in the allowed origins list.

**Fix**: Add your frontend URL to `ALLOWED_ORIGINS`:
```env
ALLOWED_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
```

#### 10. `bcrypt` / `passlib` errors

**Cause**: Incompatible bcrypt version with passlib.

**Fix**: Pin bcrypt to version 4.0.1 in `requirements.txt`:
```
bcrypt==4.0.1
passlib[bcrypt]>=1.7.4
```

Or use bcrypt directly without passlib:
```python
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
```

#### 11. Slow cold starts on Vercel

**Cause**: Large dependency bundle or heavy initialization logic.

**Fix**:
- Minimize dependencies in `requirements.txt`
- Defer heavy initialization (e.g., ML model loading) to first request rather than module import
- Consider using Vercel's Edge Functions for lightweight endpoints

#### 12. ChromaDB `PermissionError` or `ReadOnlyFileSystem` on Vercel

**Cause**: Vercel's serverless environment has a read-only filesystem.

**Fix**: ChromaDB PersistentClient cannot be used on Vercel. Options:
- Use ChromaDB Cloud (hosted)
- Use an external vector database (Pinecone, Weaviate, Qdrant)
- Disable vector search features in the Vercel deployment

---

## Production Checklist

Before deploying to production, verify the following:

- [ ] `SECRET_KEY` is a strong, unique random value (not the default)
- [ ] `DEBUG` is set to `false`
- [ ] `ENVIRONMENT` is set to `production`
- [ ] `ALLOWED_ORIGINS` contains only your actual frontend domain(s)
- [ ] `DATABASE_URL` points to a managed PostgreSQL instance with SSL enabled
- [ ] All database migrations have been applied (`alembic upgrade head`)
- [ ] Default admin password has been changed
- [ ] Error monitoring (e.g., Sentry) is configured
- [ ] Health check endpoint is monitored
- [ ] Database backups are configured (managed providers typically handle this)
- [ ] Rate limiting is configured for authentication endpoints
- [ ] HTTPS is enforced (handled by Vercel/cloud provider)
- [ ] Log level is set to `WARNING` or `INFO` (not `DEBUG`)
- [ ] Sensitive data is not logged (passwords, tokens, API keys)