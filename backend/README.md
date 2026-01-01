# Open Insurance Backend

AI-powered insurance management platform for commercial real estate.

## Tech Stack

- **Python 3.11+**
- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - Async ORM
- **Pydantic v2** - Data validation
- **PostgreSQL** - Primary database
- **Alembic** - Database migrations

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for local development)
- PostgreSQL (or use Docker)

### Local Development with Docker

1. **Start all services:**
   ```bash
   docker-compose up
   ```

2. **Access the API:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/v1/docs
   - Health: http://localhost:8000/v1/health

### Local Development with Supabase

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Update `.env` with your Supabase credentials:**
   ```
   DATABASE_URL=postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```

3. **Install dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

### Running Tests

```bash
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=term-missing
```

### Linting & Formatting

```bash
# Check linting
ruff check .

# Auto-fix linting issues
ruff check . --fix

# Format code
ruff format .
```

## Project Structure

```
backend/
├── alembic/              # Database migrations
│   ├── versions/         # Migration files
│   └── env.py           # Alembic configuration
├── app/
│   ├── api/             # API endpoints
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── router.py
│   ├── core/            # Core configuration
│   │   ├── config.py    # Settings
│   │   ├── database.py  # Database setup
│   │   └── dependencies.py
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── repositories/    # Data access layer
│   └── main.py          # FastAPI app
├── tests/               # Test files
├── docker-compose.yml   # Local development
├── Dockerfile          # Container build
├── pyproject.toml      # Project config
└── alembic.ini         # Alembic config
```

## Database Migrations

```bash
# Generate a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/v1/docs
- ReDoc: http://localhost:8000/v1/redoc
- OpenAPI JSON: http://localhost:8000/v1/openapi.json
