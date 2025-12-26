# AI Service API

Production-ready FastAPI application for crypto trading analysis and financial news sentiment analysis.

## � Current Status

✅ **Implemented Features**:

- News Article Management (CRUD, Search, Pagination)
- AI-Powered Sentiment Analysis (OpenAI GPT-4o-mini)
- Real-time Text Analysis
- Batch Processing
- Database Storage & History

⚠️ **In Development**:

- News Crawler (multi-source web scraping)
- Price History Integration (Binance API)
- News-Price Alignment Analysis
- Causal Analysis (WHY explanations)

📚 **Documentation**:

- [Frontend Integration Guide](./FE_INTEGRATION_GUIDE.md) - Complete API reference for FE
- [Quick Start for FE](./QUICK_START_FE.md) - 5-minute integration guide
- [Current Status Summary](./AI_STATUS_SUMMARY.md) - What works and what doesn't
- [Requirements Analysis](./REQUIREMENTS_ANALYSIS.md) - Full feature requirements

## �🚀 Features

- **News Article Management**: Store and retrieve financial news articles
- **Sentiment Analysis**: AI-powered sentiment analysis using OpenAI models
- **Real-time Analysis**: Analyze text sentiment on-the-fly
- **Batch Processing**: Analyze multiple texts in one request
- **RESTful API**: Clean, well-documented API endpoints
- **Async/Await**: Fully asynchronous for high performance
- **Type Safety**: Strict type hints with Pydantic v2
- **Database Migrations**: Alembic for database version control

## 🏗️ Architecture

This project follows a **Modular Monolith** architecture with clear separation of concerns:

```
app/
├── api/v1/              # API routes and endpoints
│   ├── endpoints/       # Individual endpoint modules
│   └── router.py        # Main API router
├── core/                # Core functionality
│   ├── config.py        # Configuration management
│   ├── security.py      # Authentication & authorization
│   ├── exceptions.py    # Custom exceptions
│   └── dependencies.py  # Dependency injection
├── db/                  # Database layer
│   ├── base.py          # SQLAlchemy base models
│   ├── session.py       # Async session management
│   └── models/          # SQLAlchemy models
├── schemas/             # Pydantic models (API layer)
│   ├── base.py          # Base schemas
│   ├── news.py          # News article schemas
│   └── sentiment.py     # Sentiment analysis schemas
└── services/            # Business logic layer
    ├── base.py          # Base CRUD operations
    ├── news.py          # News article CRUD
    └── sentiment.py     # Sentiment analysis CRUD
```

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL 14+ (or SQLite for development)
- Redis 6+ (optional, for caching)

## 🛠️ Installation

1. **Clone the repository**:

   ```bash
   cd /home/fat/code/cryto-final-project/ai
   ```

2. **Install dependencies**:

   ```bash
   uv sync
   # or
   pip install -e .
   ```

3. **Set up environment variables**:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize the database**:

   ```bash
   # Create initial migration
   uv run alembic revision --autogenerate -m "Initial migration"

   # Apply migrations
   uv run alembic upgrade head
   ```

## 🏃 Running the Application

### Development Mode

```bash
# Using FastAPI dev server (with hot reload)
uv run fastapi dev main.py

# Or using uvicorn directly
uv run uvicorn main:app --reload
```

### Production Mode

```bash
uv run fastapi run main.py

# Or with uvicorn
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_news.py
```

## 🎨 Code Quality

### Linting & Formatting

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Fix linting issues automatically
uv run ruff check --fix .
```

### Type Checking

```bash
uv run mypy app/
```

## 🗄️ Database Migrations

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history
```

## 🐳 Docker Support

```bash
# Build image
docker build -t ai-service .

# Run container
docker run -p 8000:8000 --env-file .env ai-service
```

## 📖 Key Design Decisions

### 1. **Async SQLAlchemy 2.0**

- Uses modern async/await patterns for non-blocking database operations
- Leverages SQLAlchemy 2.0's new query API with `select()` statements

### 2. **Pydantic v2 for Validation**

- Strict separation between Pydantic schemas (API layer) and SQLAlchemy models (DB layer)
- Uses `Annotated` for dependency injection (FastAPI best practice)
- `from_attributes=True` (formerly `orm_mode`) for ORM integration

### 3. **Lifespan Events**

- Replaces deprecated `@app.on_event()` decorators
- Manages startup/shutdown in a context manager
- Properly handles database connection pooling

### 4. **Modular Structure**

- Clear separation: API → Services → Database
- CRUD operations abstracted into reusable base classes
- Domain-driven design with bounded contexts (news, sentiment)

### 5. **Modern Tooling**

- **Ruff**: Single tool replacing black, isort, flake8
- **pydantic-settings**: Type-safe configuration management
- **structlog**: Structured logging for production monitoring

## 🔐 Security

- JWT token authentication (placeholder implementation included)
- Password hashing with bcrypt
- CORS configuration
- Input validation with Pydantic
- SQL injection prevention via SQLAlchemy

## 🚦 Environment Variables

Key environment variables (see `.env.example` for complete list):

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key (change in production!)
- `CORS_ORIGINS`: Allowed origins for CORS
- `NEWS_API_KEY`: API key for news services
- `OPENAI_API_KEY`: OpenAI API key for advanced NLP

## 📝 API Endpoints

### Health

- `GET /api/v1/health` - Health check

### News Articles

- `GET /api/v1/news` - List articles (paginated)
- `GET /api/v1/news/{id}` - Get article by ID
- `POST /api/v1/news` - Create article
- `PATCH /api/v1/news/{id}` - Update article
- `DELETE /api/v1/news/{id}` - Delete article
- `GET /api/v1/news/search?q=...` - Search articles

### Sentiment Analysis

- `POST /api/v1/sentiment/analyze` - Analyze text sentiment (real-time)
- `GET /api/v1/sentiment` - List sentiment analyses
- `GET /api/v1/sentiment/{id}` - Get analysis by ID
- `POST /api/v1/sentiment` - Create analysis record
- `GET /api/v1/sentiment/news/{article_id}` - Get analyses for article

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Run `ruff format` and `ruff check` before committing
4. Update documentation as needed

## 📄 License

[Your License Here]

## 👥 Authors

Fat & Team
