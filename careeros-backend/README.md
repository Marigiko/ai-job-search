# CareerOS Backend

FastAPI + SQLAlchemy 2.0 async backend for the CareerOS job-search operating system.

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Copy environment config
cp .env.example .env

# Run migrations
alembic upgrade head

# Start development server
python -m app.main
```

## Project Structure

```
app/
├── api/           # FastAPI routers and endpoints
│   ├── deps.py    # Dependency injection
│   └── v1/        # API version 1
├── config/        # Pydantic settings
├── core/          # Logging, exceptions, shared utilities
├── models/        # SQLAlchemy ORM models
├── plugins/       # Portal search plugin system
├── schemas/       # Pydantic request/response schemas
├── services/      # Business logic layer
├── database.py    # Async engine + session factory
└── main.py        # Application factory with lifespan
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET/POST | `/api/v1/jobs` | List / create jobs |
| GET/PATCH/DELETE | `/api/v1/jobs/{id}` | Job detail operations |
| GET | `/api/v1/pipeline` | Pipeline stage counts |
| GET | `/api/v1/pipeline/kanban` | Kanban board data |
| POST | `/api/v1/outreach/compose` | Compose email |
| POST | `/api/v1/outreach/send` | Send email now |
| POST/GET | `/api/v1/outreach/queue` | Queue management |
| GET/POST | `/api/v1/templates` | Email templates |
| POST | `/api/v1/search` | Trigger portal search |
| GET | `/api/v1/analytics/*` | Metrics endpoints |

## Testing

```bash
pytest
```

## Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```
