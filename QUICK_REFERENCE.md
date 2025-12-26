# Quick Reference Guide

## 🚀 Common Commands

### Running the Application

```bash
# Development (with hot reload)
uv run uvicorn main:app --reload

# Production
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Database Migrations

```bash
# Create migration
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1

# View history
uv run alembic history
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint
uv run ruff check .

# Fix automatically
uv run ruff check --fix .

# Type check
uv run mypy app/
```

### Testing

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=app --cov-report=html

# Specific test
uv run pytest tests/test_news.py
```

### Dependencies

```bash
# Install all dependencies
uv sync

# Install with dev tools
uv sync --all-extras

# Add new dependency
uv add package-name

# Add dev dependency
uv add --dev package-name
```

## 📁 File Locations

| Purpose          | Location                    |
| ---------------- | --------------------------- |
| API Routes       | `app/api/v1/endpoints/*.py` |
| Database Models  | `app/db/models/*.py`        |
| Pydantic Schemas | `app/schemas/*.py`          |
| Business Logic   | `app/services/*.py`         |
| Configuration    | `app/core/config.py`        |
| Dependencies     | `app/core/dependencies.py`  |
| Exceptions       | `app/core/exceptions.py`    |
| Security         | `app/core/security.py`      |
| Main App         | `main.py`                   |

## 🔧 Adding a New Feature

### 1. Create Database Model

```python
# app/db/models/your_model.py
from app.db.base import Base, TimestampMixin

class YourModel(Base, TimestampMixin):
    __tablename__ = "your_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
```

### 2. Create Pydantic Schemas

```python
# app/schemas/your_schema.py
from app.schemas.base import BaseSchema

class YourModelCreate(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)

class YourModelResponse(YourModelCreate):
    id: int
    created_at: datetime
    updated_at: datetime
```

### 3. Create CRUD Service

```python
# app/services/your_service.py
from app.services.base import CRUDBase

class CRUDYourModel(CRUDBase[YourModel, YourModelCreate, YourModelUpdate]):
    pass

your_model = CRUDYourModel(YourModel)
```

### 4. Create API Endpoints

```python
# app/api/v1/endpoints/your_endpoint.py
from fastapi import APIRouter
from app.core.dependencies import DBSession

router = APIRouter()

@router.get("", response_model=list[YourModelResponse])
async def get_items(db: DBSession):
    items = await your_model.get_multi(db)
    return items
```

### 5. Register Router

```python
# app/api/v1/router.py
from app.api.v1.endpoints import your_endpoint

api_router.include_router(
    your_endpoint.router,
    prefix="/your-endpoint",
    tags=["Your Feature"]
)
```

### 6. Create Migration

```bash
uv run alembic revision --autogenerate -m "Add your_table"
uv run alembic upgrade head
```

## 🔐 Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Application
DEBUG=true
ENVIRONMENT=development

# Database
DATABASE_HOST=localhost
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password
DATABASE_NAME=ai_service

# Security
SECRET_KEY=your-secret-key-min-32-chars

# External APIs
NEWS_API_KEY=your-api-key
OPENAI_API_KEY=your-openai-key
```

## 🐛 Common Issues

### Issue: Module not found

```bash
# Solution: Reinstall dependencies
uv sync
```

### Issue: Database connection error

```bash
# Solution: Check DATABASE_URL in .env
# Make sure PostgreSQL is running
```

### Issue: Migration conflicts

```bash
# Solution: Reset migrations (DEV ONLY!)
uv run alembic downgrade base
uv run alembic upgrade head
```

### Issue: Import errors in IDE

```bash
# Solution: Select the correct Python interpreter
# Should be: .venv/bin/python
```

## 📚 Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **Pydantic v2**: https://docs.pydantic.dev/latest/
- **Alembic**: https://alembic.sqlalchemy.org/
- **Ruff**: https://docs.astral.sh/ruff/

## 💡 Tips

1. **Always use type hints** - It helps with IDE autocomplete and catches bugs early
2. **Keep schemas and models separate** - Schemas are for API, models are for database
3. **Use dependency injection** - Makes testing easier
4. **Write migrations, don't skip them** - Makes deployments smooth
5. **Format before committing** - Run `ruff format .` and `ruff check --fix .`
6. **Test your endpoints** - Use the `/docs` page to test interactively
