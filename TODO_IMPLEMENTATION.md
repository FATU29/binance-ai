# TODO List - AI Service Implementation

## 🎯 Tóm Tắt Nhanh

### ✅ Đã Xong (Có thể dùng ngay)

- [x] Sentiment Analysis với OpenAI
- [x] News Management (CRUD)
- [x] Database models cho News & Sentiment
- [x] API endpoints cơ bản
- [x] Documentation cho FE integration

### ❌ Cần Làm Gấp

- [ ] News Crawler
- [ ] Price History Service
- [ ] Binance API Integration
- [ ] News-Price Alignment
- [ ] Causal Analysis
- [ ] VIP Feature Gating

---

## 📋 Chi Tiết Tasks

### Priority 1: Critical (Cần làm trước)

#### 1. Implement Price History Service

**Files cần tạo/sửa**:

- `app/db/models/price_history.py` (hiện tại: EMPTY)
- `app/services/binance_service.py` (hiện tại: EMPTY)
- `app/services/price_history.py` (hiện tại: EMPTY)
- `app/schemas/price_history.py` (chưa tạo)
- `app/api/v1/endpoints/price_history.py` (chưa tạo)

**Tasks**:

```bash
1. Tạo PriceHistory model trong database
2. Viết service fetch data từ Binance API
3. Tạo endpoint GET /api/v1/prices/{symbol}
4. Tạo background task để sync price định kỳ
5. Test với BTCUSDT và ETHUSDT
```

**Estimate**: 1-2 ngày

---

#### 2. Implement Basic News Crawler

**Files cần tạo**:

- `app/services/crawler_service.py` (chưa có)
- `app/services/html_parser.py` (chưa có)
- `app/core/crawler_config.py` (chưa có)
- `app/api/v1/endpoints/crawler.py` (chưa có)

**Tasks**:

```bash
1. Install dependencies: beautifulsoup4, feedparser
2. Tạo RSS feed parser cho CoinDesk, CoinTelegraph
3. Tạo HTML scraper cơ bản
4. Implement scheduled crawling (APScheduler)
5. Test crawler với 2-3 nguồn
```

**Estimate**: 2-3 ngày

---

### Priority 2: Important (Làm tiếp sau)

#### 3. Implement News-Price Alignment

**Files cần sửa**:

- `app/services/alignment_service.py` (hiện tại: EMPTY)
- `app/schemas/alignment.py` (chưa tạo)
- `app/api/v1/endpoints/alignment.py` (chưa tạo)
- `app/db/models/alignment.py` (chưa tạo - optional)

**Tasks**:

```bash
1. Viết logic align news time với price time
2. Tính correlation giữa sentiment và price change
3. Tạo API endpoint để FE query alignment
4. Prepare features cho ML models (nếu cần)
```

**Estimate**: 2-3 ngày

---

#### 4. Implement VIP Feature Gating

**Files cần sửa**:

- `app/core/security.py` (có sẵn nhưng minimal)
- `app/core/dependencies.py` (cần thêm role checking)
- Tất cả endpoints cần restrict (add VIP dependency)

**Tasks**:

```bash
1. Implement JWT token verification
2. Tạo UserRole enum (Regular, VIP, Admin)
3. Tạo require_vip() dependency
4. Apply vào các endpoints advanced (causal analysis, etc.)
5. Test với mock tokens
```

**Estimate**: 1 ngày

---

### Priority 3: Advanced (Làm sau cùng)

#### 5. Implement Causal Analysis

**Files cần tạo**:

- `app/services/causal_analysis_service.py` (chưa có)
- `app/schemas/causal_analysis.py` (chưa có)
- `app/api/v1/endpoints/causal.py` (chưa có)

**Tasks**:

```bash
1. Design prompt template cho OpenAI
2. Implement explain_price_movement()
3. Tạo API endpoint POST /ai/causal/explain
4. Add caching cho causal explanations
5. Test với real price movements
```

**Estimate**: 2-3 ngày

---

#### 6. Intelligent Crawler Enhancement

**Files cần sửa**:

- `app/services/crawler_service.py`
- `app/services/html_parser.py`

**Tasks**:

```bash
1. Implement structure detection algorithm
2. Add adaptive parsing khi website thay đổi
3. Add error handling & retry logic
4. Implement rate limiting
5. Add monitoring & logging
```

**Estimate**: 3-4 ngày

---

## 🔧 Quick Fixes (Có thể làm ngay)

### Fix 1: Add OpenAI API Key Check

**File**: `app/core/config.py`

```python
# Add validation
@validator("OPENAI_API_KEY")
def validate_openai_key(cls, v):
    if not v or v == "your_openai_api_key_here":
        logger.warning("⚠️ OpenAI API key not set! Sentiment analysis will use fallback.")
    return v
```

---

### Fix 2: Add Health Check for OpenAI

**File**: `app/api/v1/endpoints/health.py`

```python
@router.get("/detailed")
async def detailed_health():
    return {
        "status": "healthy",
        "openai_available": bool(settings.OPENAI_API_KEY),
        "database_connected": True,  # Check DB connection
        "features": {
            "sentiment_analysis": True,
            "news_management": True,
            "price_history": False,
            "news_crawler": False,
            "alignment": False,
            "causal_analysis": False
        }
    }
```

---

### Fix 3: Add CORS for Frontend

**File**: `main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📝 Database Migrations Needed

### Migration 1: Add price_history table

```bash
cd ai
uv run alembic revision --autogenerate -m "Add price_history table"
uv run alembic upgrade head
```

### Migration 2: Add alignment table (optional)

```bash
uv run alembic revision --autogenerate -m "Add news_price_alignment table"
uv run alembic upgrade head
```

### Migration 3: Add causal_analysis table (optional)

```bash
uv run alembic revision --autogenerate -m "Add causal_analysis table"
uv run alembic upgrade head
```

---

## 🧪 Testing Checklist

### Current Features (Test Now)

- [ ] POST /news - Create article
- [ ] GET /news - List articles
- [ ] GET /news/{id} - Get single article
- [ ] POST /ai/analyze/quick - Quick sentiment
- [ ] POST /ai/analyze/news/{id} - Analyze article
- [ ] GET /ai/news/{id}/latest - Get sentiment

### Future Features (Test Later)

- [ ] POST /crawler/run - Manual crawl trigger
- [ ] GET /prices/{symbol} - Get price history
- [ ] POST /alignment/analyze - Alignment analysis
- [ ] POST /causal/explain - Causal explanation

---

## 📦 Dependencies to Add

**Add to `pyproject.toml`**:

```toml
[project]
dependencies = [
    # ... existing ...

    # Web Scraping
    "beautifulsoup4>=4.12.0",
    "lxml>=5.0.0",
    "feedparser>=6.0.0",
    "playwright>=1.40.0",  # For JS-heavy sites

    # Background Tasks
    "apscheduler>=3.10.0",

    # Data Processing
    "pandas>=2.1.0",
    "numpy>=1.26.0",
]
```

**Install**:

```bash
cd ai
uv sync
```

---

## 🚀 Deployment Checklist

### Before Deploy:

- [ ] Set OPENAI_API_KEY in production .env
- [ ] Run database migrations
- [ ] Test all endpoints
- [ ] Add CORS for production FE URL
- [ ] Set up logging
- [ ] Add error monitoring (Sentry?)

### Docker Setup:

- [ ] Update dockerfile if needed
- [ ] Update docker-compose.yml
- [ ] Test Docker build
- [ ] Test Docker run

---

## 📞 Support

**When stuck, check**:

- API Docs: http://localhost:8000/docs
- FE Integration Guide: `FE_INTEGRATION_GUIDE.md`
- Status Summary: `AI_STATUS_SUMMARY.md`
- Requirements: `REQUIREMENTS_ANALYSIS.md`

**Contact**: Team Lead / Project Manager

---

**Last Updated**: December 25, 2025
**Priority**: Start with Priority 1 tasks!
