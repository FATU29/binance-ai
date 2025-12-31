# 📝 AI Service - Changes Note

**Date**: 2025-12-30

## ⚠️ Important Changes

### 1. Code Restored ✅

- **Original `main.py`**: Đã được restore từ git history
- **New simple version**: Saved as `main_simple.py` (tham khảo)

### 2. Your Existing AI Service (Original)

**Structure**:
```
ai/
├── main.py              # ✅ RESTORED - Entry point chính
├── app/                 # ✅ Your existing code
│   ├── api/v1/         # API endpoints
│   │   ├── endpoints/
│   │   │   ├── ai_analytics.py
│   │   │   ├── health.py
│   │   │   ├── news.py
│   │   │   └── sentiment.py
│   │   └── router.py
│   ├── core/           # Config, security, exceptions
│   ├── db/             # SQLAlchemy models & session
│   ├── schemas/        # Pydantic schemas
│   └── services/       # Business logic services
├── pyproject.toml      # Dependencies (using uv)
├── dockerfile          # Docker configuration
└── alembic/           # Database migrations
```

**Features**:
- ✅ FastAPI with SQLAlchemy 2.0 (async)
- ✅ PostgreSQL with asyncpg
- ✅ Redis for caching
- ✅ OpenAI integration
- ✅ Structured logging
- ✅ Database migrations (Alembic)
- ✅ Security (JWT, passlib)
- ✅ CORS configuration

### 3. Simple AI Service (New - Reference Only)

**File**: `main_simple.py`

**Features**:
- Simple FastAPI app
- FinBERT sentiment analysis
- BERT NER entity extraction
- Price impact prediction
- No database (stateless)

**Use case**: Quick testing, standalone sentiment analysis

## 🐛 Docker Build Fix

### Problem
```
Failed to download `hiredis==3.3.0`
Failed to download distribution due to network timeout. 
Try increasing UV_HTTP_TIMEOUT (current value: 30s).
```

### Solution Applied ✅

Updated `dockerfile`:
```dockerfile
# Install dependencies with increased timeout
ENV UV_HTTP_TIMEOUT=120
RUN uv sync --frozen --no-cache
```

### Alternative Solution (if still fails)

If Docker build still times out, you can:

**Option 1**: Remove hiredis (it's optional)

Edit `pyproject.toml`:
```toml
# Change from:
"redis[hiredis]>=5.0.0",

# To:
"redis>=5.0.0",
```

Then update lock file:
```bash
uv lock
```

**Option 2**: Build with host network (faster downloads)

```bash
docker build --network=host -t ai-service -f dockerfile .
```

**Option 3**: Pre-download dependencies locally

```bash
# Install locally first
uv sync

# Then build Docker (will use cache)
docker build -t ai-service -f dockerfile .
```

## 🚀 How to Run

### Local Development

```bash
# Install dependencies
uv sync

# Run migrations (if database configured)
uv run alembic upgrade head

# Start server
uv run python main.py

# Or with uvicorn directly
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build
docker build -t ai-service -f dockerfile .

# Run
docker run -p 8000:8000 ai-service

# Or with environment variables
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  -e REDIS_URL="redis://..." \
  -e OPENAI_API_KEY="..." \
  ai-service
```

### Docker Compose (Recommended)

If you have `docker-compose.yml` in the root project:

```bash
cd /home/fat/code/cryto-final-project
docker-compose up -d ai-service
```

## 📊 API Endpoints

Your existing service has these endpoints:

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### News Operations
```bash
# Get news
GET /api/v1/news

# Create news
POST /api/v1/news

# Get news by ID
GET /api/v1/news/{id}
```

### Sentiment Analysis
```bash
# Analyze text sentiment
POST /api/v1/sentiment/analyze

# Batch analysis
POST /api/v1/sentiment/batch
```

### AI Analytics
```bash
# Get AI analytics
GET /api/v1/ai-analytics
```

## 🔑 Environment Variables

Create `.env` file:

```bash
# Application
APP_NAME="AI Service API"
APP_VERSION="0.1.0"
DEBUG=false
LOG_LEVEL=INFO

# API
API_V1_PREFIX="/api/v1"

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Database
DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dbname"

# Redis
REDIS_URL="redis://localhost:6379/0"

# OpenAI (if using)
OPENAI_API_KEY="sk-..."

# Security
SECRET_KEY="your-secret-key-here"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 📚 Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## 🔄 Integration with Golang Backend

Your AI service can be called from the Golang crawler service:

```go
// In ai_service.go
resp, err := http.Post(
    "http://localhost:8000/api/v1/sentiment/analyze",
    "application/json",
    bytes.NewBuffer(jsonData),
)
```

## 🆚 Comparison: Original vs Simple

| Feature | Original (main.py) | Simple (main_simple.py) |
|---------|-------------------|-------------------------|
| Framework | FastAPI + SQLAlchemy | FastAPI only |
| Database | PostgreSQL (async) | None |
| Redis | Yes | No |
| OpenAI | Yes | No (uses Transformers) |
| AI Models | OpenAI GPT | FinBERT, BERT NER |
| Migrations | Alembic | No |
| Authentication | JWT | No |
| Production Ready | ✅ Yes | ⚠️ Basic |

## 🎯 Recommendation

**Use Original (main.py)** if:
- ✅ You need database persistence
- ✅ You want to store news articles
- ✅ You need user authentication
- ✅ You're using OpenAI API
- ✅ Production deployment

**Use Simple (main_simple.py)** if:
- ✅ Quick testing only
- ✅ Stateless sentiment analysis
- ✅ No database available
- ✅ Learning/prototyping

## 🔧 Troubleshooting

### Cannot connect to database
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -U postgres -h localhost -d crypto_news
```

### Redis connection failed
```bash
# Check if Redis is running
docker ps | grep redis

# Test connection
redis-cli ping
```

### Import errors
```bash
# Reinstall dependencies
uv sync --reinstall

# Or clean and reinstall
rm -rf .venv
uv sync
```

## ✅ Summary

1. ✅ **Original code RESTORED** - Your full-featured AI service
2. ✅ **Simple version SAVED** as `main_simple.py` for reference
3. ✅ **Docker build FIXED** - Increased UV_HTTP_TIMEOUT to 120s
4. ✅ **Documentation ADDED** - This file!

---

*If you have any questions or need help, refer to the FastAPI documentation: https://fastapi.tiangolo.com/*

