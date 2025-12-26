# AI Service Requirements Analysis

## 📋 Project Overview

**Project**: Crypto Trading Platform - AI Service
**Focus**: AI-related features only (News Crawling, Sentiment Analysis, Price-News Alignment, Causal Analysis)
**Trading Pair**: BTCUSDT, ETHUSDT, and other configurable pairs

---

## ✅ Current Implementation Status

### 1. News Collection & Crawling (Requirement 1) ⚠️ **PARTIALLY IMPLEMENTED**

#### Requirement Details:

> Thu thập tin tức tài chính (từ nhiều nguồn khác nhau) => Crawler
>
> - Xác định lấy những thông tin gì cần thiết cho việc phân tích dữ liệu
> - Mỗi trang có cấu trúc html khác nhau => tự động học được structure của mỗi trang để tự động trích xuất được thông tin
> - Lưu ý trường hợp các trang thay đổi cấu trúc html
> - Dữ liệu lưu trữ đầy đủ, hiển thị lên GUI có chọn lọc

#### Current Implementation:

✅ **Implemented Features:**

- Database model for news storage (`app/db/models/news.py`)
  - Fields: `id`, `title`, `content`, `source`, `url`, `author`, `published_at`, `category`
  - Proper timestamps with `TimestampMixin`
  - Unique URL constraint to prevent duplicates
- CRUD operations for news articles (`app/services/news.py`)
  - Get by URL
  - Get by category
  - Search by title/content
- API endpoints for news management (`app/api/v1/endpoints/news.py`)
  - Create news article
  - Read news article
  - List news articles
  - Update/delete operations

❌ **MISSING Critical Features:**

1. **No Actual Web Crawler Implementation**

   - No scraper/crawler service exists
   - No multi-source news fetching
   - No RSS feed integration
   - No scheduled crawling tasks

2. **No Intelligent HTML Structure Learning**

   - No automatic HTML structure detection
   - No adaptive parsing logic
   - No handling of website structure changes
   - Missing: BeautifulSoup/Scrapy integration
   - Missing: Machine learning-based structure learning

3. **No Source Configuration Management**

   - No list of target news sources (CoinDesk, CoinTelegraph, Bloomberg, etc.)
   - No source-specific parsing rules
   - No source priority/reliability scoring

4. **No Data Extraction Strategy**
   - Unclear which fields are essential for analysis
   - No metadata extraction (tags, related symbols, impact score)
   - No image/media handling

#### Recommendations:

```python
# TODO: Implement missing components
# 1. Create app/services/crawler_service.py
#    - Multi-source news fetching
#    - RSS feed parsing
#    - HTML structure learning
#    - Adaptive parsing with fallback

# 2. Create app/services/html_parser_service.py
#    - Automatic structure detection using ML/heuristics
#    - Template-based parsing
#    - Change detection and adaptation

# 3. Create app/core/crawler_config.py
#    - Define news sources (URLs, types, parsing rules)
#    - Configure crawl frequency
#    - Define essential fields for extraction

# 4. Add background task scheduler (Celery/APScheduler)
#    - Schedule periodic crawling
#    - Handle retries and rate limiting
#    - Monitor crawler health
```

---

### 2. Price Charts & WebSocket (Requirement 2) ✅ **NOT AI RESPONSIBILITY**

This is handled by the frontend (`fe/`) and backend (`binance-final-project-chart-backend/`).
AI service does NOT need to implement this.

**Note**: AI service only needs to consume historical price data for analysis.

---

### 3. AI Models for News Analysis (Requirement 3) ✅ **IMPLEMENTED** ⚠️ **NEEDS ENHANCEMENT**

#### Requirement Details:

> Sử dụng các mô hình AI để phân tích tin tức
>
> - Align tin tức kèm giá lịch sử để đưa vào mô hình AI
> - Sử dụng các mô hình AI có sẵn (hộp đen)
> - Phân tích có tính nhân quả (Nâng cao): Xu hướng giờ/ngày kết tiếp UP/DOWN => lý do vì sao

#### Current Implementation:

##### 3.1 Sentiment Analysis ✅ **FULLY IMPLEMENTED**

**File**: `app/services/sentiment_service.py`

✅ **Implemented Features:**

- OpenAI GPT-4o-mini integration for sentiment analysis
- Structured JSON responses with sentiment classification
- Financial/crypto-specific sentiment labels:
  - `bullish`, `bearish`, `neutral`, `positive`, `negative`
- Sentiment score (0.0 to 1.0) and confidence scoring
- Key factors extraction (reasoning behind sentiment)
- Fallback keyword-based analysis when OpenAI unavailable
- Comprehensive crypto/financial keyword dictionary

**API Endpoints** (`app/api/v1/endpoints/ai_analytics.py`):

- `POST /api/v1/ai/analyze/news/{article_id}` - Analyze news article and save
- `POST /api/v1/ai/analyze/batch` - Batch text analysis
- `POST /api/v1/ai/analyze/quick` - Quick analysis without DB save
- `GET /api/v1/ai/news/{article_id}/latest` - Get latest sentiment

**Database Model** (`app/db/models/sentiment.py`):

- Fields: `sentiment_label`, `sentiment_score`, `confidence`, `model_version`, `analysis_metadata`
- Foreign key to news articles
- Proper timestamps

##### 3.2 News-Price Alignment ❌ **NOT IMPLEMENTED**

**Current Status**: `app/services/alignment_service.py` exists but is **EMPTY**

❌ **MISSING Critical Features:**

1. **No Price History Integration**

   - Missing: `app/db/models/price_history.py` (file exists but empty)
   - No table to store historical price data
   - No service to fetch price data from Binance API
   - No correlation with news timestamps

2. **No Alignment Logic**

   - No time-based news-price alignment
   - No correlation calculation
   - No window-based analysis (e.g., sentiment before/after price movement)
   - No lag analysis (delayed price impact)

3. **No Feature Engineering**
   - No aggregated sentiment scores over time windows
   - No price movement features (% change, volatility)
   - No combined features for ML input

#### Recommendations:

##### Implement Price History Service:

```python
# TODO: app/db/models/price_history.py
class PriceHistory(Base, TimestampMixin):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)  # BTCUSDT
    timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    interval: Mapped[str] = mapped_column(String(10), nullable=False)  # 1m, 5m, 1h, 1d

    # Composite unique constraint
    __table_args__ = (
        UniqueConstraint('symbol', 'timestamp', 'interval', name='uix_symbol_timestamp_interval'),
    )

# TODO: app/services/price_history.py
class PriceHistoryService:
    async def fetch_and_store_binance_klines(
        self,
        symbol: str,
        interval: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[PriceHistory]:
        """Fetch historical klines from Binance and store in DB"""
        pass

    async def get_price_at_time(
        self,
        symbol: str,
        timestamp: datetime,
        interval: str = "1h"
    ) -> PriceHistory | None:
        """Get price data closest to specified timestamp"""
        pass
```

##### Implement Alignment Service:

```python
# TODO: app/services/alignment_service.py
class AlignmentService:
    """Align news sentiment with price movements for correlation analysis"""

    async def align_news_with_price(
        self,
        news_article_id: int,
        symbol: str,
        time_window_before: timedelta = timedelta(hours=1),
        time_window_after: timedelta = timedelta(hours=24)
    ) -> AlignmentResult:
        """
        Align a news article with price movements.

        Returns:
        - Price before news
        - Price after news
        - Price change %
        - Sentiment score
        - Correlation strength
        """
        pass

    async def calculate_correlation(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        time_window: timedelta = timedelta(hours=6)
    ) -> CorrelationAnalysis:
        """
        Calculate correlation between sentiment and price movements
        over a time period.
        """
        pass

    async def prepare_ml_features(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Prepare feature matrix for ML models.

        Features:
        - Aggregated sentiment score (rolling average)
        - Sentiment momentum (change rate)
        - Price features (returns, volatility, momentum)
        - Time features (hour, day of week, etc.)
        """
        pass
```

##### 3.3 Causal Analysis (Advanced) ❌ **NOT IMPLEMENTED**

**Current Status**: No implementation exists

❌ **MISSING Critical Features:**

1. **No Causal Inference Framework**

   - No causal model implementation
   - No treatment/outcome definition
   - No confounding factor control

2. **No Reasoning Engine**

   - No "WHY" explanation generation
   - No causal chain analysis
   - No event attribution

3. **No Interpretability Layer**
   - No human-readable explanations
   - No confidence scoring for causal claims

#### Recommendations:

##### Approach 1: LLM-based Causal Reasoning (Simpler, Recommended)

```python
# TODO: app/services/causal_analysis_service.py
class CausalAnalysisService:
    """
    Use LLM (OpenAI GPT-4) to generate causal explanations.

    This is simpler and more practical than implementing
    formal causal inference methods.
    """

    async def explain_price_movement(
        self,
        symbol: str,
        timestamp: datetime,
        price_change: float,
        news_context: List[NewsArticle],
        time_window: timedelta = timedelta(hours=24)
    ) -> CausalExplanation:
        """
        Generate causal explanation for price movement.

        Process:
        1. Fetch price movement data
        2. Fetch relevant news in time window
        3. Construct prompt with context
        4. Ask LLM to identify likely causes
        5. Rank causes by confidence
        """

        prompt = f"""
        You are a financial analyst expert in cryptocurrency markets.

        Context:
        - Symbol: {symbol}
        - Time: {timestamp}
        - Price Movement: {price_change:+.2f}%
        - Time Window: {time_window}

        Recent News:
        {self._format_news_context(news_context)}

        Task: Analyze the causal relationship between the news and price movement.

        Provide:
        1. Most likely cause(s) for the price movement
        2. Confidence score (0-1) for each cause
        3. Supporting evidence from news
        4. Alternative explanations
        5. Overall causal strength (Strong/Moderate/Weak/None)

        Respond in JSON format.
        """

        # Call OpenAI API
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        return CausalExplanation.model_validate_json(response.choices[0].message.content)

    async def analyze_trend_causality(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        trend: Literal["UP", "DOWN", "SIDEWAYS"]
    ) -> TrendCausalAnalysis:
        """
        Explain WHY a trend (hourly/daily) is UP/DOWN.

        Aggregates multiple causal explanations over the trend period.
        """
        pass
```

##### Approach 2: Statistical Causal Inference (Advanced, Complex)

```python
# Alternative advanced approach (requires more effort)
# Using libraries like: DoWhy, CausalML, EconML

from dowhy import CausalModel

class AdvancedCausalAnalysisService:
    """
    Formal causal inference using statistical methods.

    Warning: This is significantly more complex and requires:
    - Proper causal graph definition
    - Identification of confounders
    - Sufficient data for statistical power
    - Expertise in causal inference
    """

    async def estimate_causal_effect(
        self,
        treatment: str,  # e.g., "positive_sentiment"
        outcome: str,    # e.g., "price_increase"
        data: pd.DataFrame
    ) -> CausalEstimate:
        """
        Estimate causal effect using methods like:
        - Propensity Score Matching
        - Instrumental Variables
        - Difference-in-Differences
        - Regression Discontinuity
        """
        pass
```

**Recommendation**: Start with **Approach 1 (LLM-based)** for faster implementation and better explainability. Move to Approach 2 only if rigorous causal inference is required.

---

### 4. Account Management (Requirement 4) ✅ **NOT AI RESPONSIBILITY**

This is handled by the authentication system in the main backend.
AI service only needs to:

- Verify user authentication (check JWT tokens)
- Differentiate between regular/VIP users
- Restrict advanced AI features to VIP users

#### Current Implementation:

⚠️ **Partially Ready**:

- Security module exists: `app/core/security.py`
- Dependencies for auth exist: `app/core/dependencies.py`

❌ **MISSING**:

- No actual user role checking
- No VIP feature gating
- No integration with main auth service

#### Recommendations:

```python
# TODO: app/core/dependencies.py
from enum import Enum

class UserRole(str, Enum):
    REGULAR = "regular"
    VIP = "vip"
    ADMIN = "admin"

async def get_current_user_role(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> UserRole:
    """Extract user role from JWT token"""
    # Verify token and extract claims
    pass

def require_vip(
    user_role: Annotated[UserRole, Depends(get_current_user_role)]
) -> None:
    """Dependency to restrict endpoint to VIP users"""
    if user_role not in [UserRole.VIP, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature requires VIP access"
        )

# Usage in endpoints:
@router.post("/ai/analyze/causal")
async def causal_analysis(
    _: Annotated[None, Depends(require_vip)],  # VIP only
    ...
):
    """Advanced causal analysis - VIP feature"""
    pass
```

---

## 🚨 Critical Missing Components Summary

### High Priority (Must Implement):

1. **News Crawler System** ❌

   - Multi-source web scraping
   - Intelligent HTML parsing
   - Adaptive structure learning
   - Scheduled crawling

2. **Price History Service** ❌

   - Database model for price data
   - Binance API integration
   - Historical data fetching and storage

3. **News-Price Alignment Service** ❌

   - Time-based correlation
   - Feature engineering for ML
   - Alignment API endpoints

4. **Causal Analysis Service** ❌
   - LLM-based causal reasoning
   - WHY explanations for price movements
   - Trend causality analysis

### Medium Priority:

5. **User Role & VIP Gating** ⚠️

   - JWT token verification
   - Role-based access control
   - VIP feature restrictions

6. **Enhanced Sentiment Analysis** ⚠️
   - Symbol-specific sentiment (Bitcoin vs Ethereum)
   - Multi-language support
   - Sentiment aggregation over time

### Low Priority (Nice to Have):

7. **Monitoring & Logging**

   - Crawler health monitoring
   - API usage analytics
   - Model performance tracking

8. **Caching Layer**
   - Redis caching for frequent queries
   - Sentiment result caching

---

## 📊 Database Schema Status

### Existing Tables:

✅ `news_articles` - Fully implemented
✅ `sentiment_analyses` - Fully implemented

### Missing Tables:

❌ `price_history` - **MUST CREATE**
❌ `alignments` - **RECOMMENDED** (for storing alignment results)
❌ `causal_analyses` - **RECOMMENDED** (for caching causal explanations)
❌ `crawler_sources` - **RECOMMENDED** (for managing news sources)
❌ `crawler_logs` - **RECOMMENDED** (for monitoring crawler runs)

### Recommended Schema:

```python
# TODO: app/db/models/price_history.py
class PriceHistory(Base, TimestampMixin):
    """Store historical price data from exchanges"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    interval: str  # 1m, 5m, 1h, 1d

# TODO: app/db/models/alignment.py
class NewsPriceAlignment(Base, TimestampMixin):
    """Store news-price alignment analysis results"""
    news_article_id: int
    symbol: str
    price_before: float
    price_after: float
    price_change_percent: float
    time_window_hours: int
    correlation_score: float
    sentiment_score: float

# TODO: app/db/models/causal_analysis.py
class CausalAnalysis(Base, TimestampMixin):
    """Store causal analysis results"""
    symbol: str
    timestamp: datetime
    price_change_percent: float
    trend: str  # UP, DOWN, SIDEWAYS
    primary_cause: str
    confidence: float
    supporting_evidence: str  # JSON
    explanation: str  # Human-readable explanation

# TODO: app/db/models/crawler_source.py
class CrawlerSource(Base, TimestampMixin):
    """Manage news sources for crawler"""
    name: str
    url: str
    source_type: str  # RSS, HTML, API
    parsing_config: str  # JSON
    is_active: bool
    crawl_frequency_minutes: int
    last_crawled_at: datetime
```

---

## 🎯 Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

- [ ] Create `PriceHistory` model and service
- [ ] Integrate Binance API for historical data
- [ ] Create database migrations
- [ ] Implement price data fetching endpoints

### Phase 2: News Crawler (Week 2-3)

- [ ] Design crawler architecture
- [ ] Implement basic HTML scraper
- [ ] Add RSS feed support
- [ ] Create `CrawlerSource` management
- [ ] Schedule periodic crawling
- [ ] Add error handling and logging

### Phase 3: Intelligent Parsing (Week 3-4)

- [ ] Implement structure detection algorithm
- [ ] Add template-based parsing
- [ ] Create fallback mechanisms
- [ ] Handle website changes
- [ ] Test with multiple news sources

### Phase 4: Alignment Service (Week 4-5)

- [ ] Implement time-based alignment
- [ ] Calculate correlation metrics
- [ ] Create alignment API endpoints
- [ ] Add visualization data endpoints

### Phase 5: Causal Analysis (Week 5-6)

- [ ] Design causal analysis architecture
- [ ] Implement LLM-based reasoning
- [ ] Create explanation generation
- [ ] Add trend causality analysis
- [ ] Create causal analysis endpoints

### Phase 6: VIP Features & Polish (Week 6-7)

- [ ] Implement user role checking
- [ ] Add VIP feature gating
- [ ] Enhance error handling
- [ ] Add comprehensive logging
- [ ] Create admin monitoring dashboard

### Phase 7: Testing & Documentation (Week 7-8)

- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Performance testing
- [ ] Update API documentation
- [ ] Create user guides

---

## 📝 API Endpoints to Implement

### News Crawler Endpoints:

```
POST   /api/v1/crawler/sources          # Add news source
GET    /api/v1/crawler/sources          # List sources
PUT    /api/v1/crawler/sources/{id}     # Update source
DELETE /api/v1/crawler/sources/{id}     # Remove source
POST   /api/v1/crawler/run               # Manually trigger crawl
GET    /api/v1/crawler/status            # Crawler status
```

### Price History Endpoints:

```
GET    /api/v1/prices/{symbol}           # Get price history
POST   /api/v1/prices/fetch              # Fetch and store prices
GET    /api/v1/prices/{symbol}/latest    # Get latest price
```

### Alignment Endpoints:

```
POST   /api/v1/alignment/analyze         # Create alignment analysis
GET    /api/v1/alignment/{symbol}        # Get alignments for symbol
GET    /api/v1/alignment/correlation     # Get correlation metrics
```

### Causal Analysis Endpoints (VIP Only):

```
POST   /api/v1/causal/explain            # Explain price movement
GET    /api/v1/causal/{symbol}/trend     # Analyze trend causality
GET    /api/v1/causal/history            # Get past analyses
```

---

## 🔧 Technology Stack Additions

### Required Libraries:

```toml
# Add to pyproject.toml

# Web Scraping & Parsing
beautifulsoup4 = "^4.12.0"
lxml = "^5.0.0"
feedparser = "^6.0.0"
scrapy = "^2.11.0"  # Optional: for advanced crawling
playwright = "^1.40.0"  # For JavaScript-heavy sites

# HTTP Clients
httpx = "^0.25.0"  # Already included
aiohttp = "^3.9.0"

# Data Processing
pandas = "^2.1.0"
numpy = "^1.26.0"

# Background Tasks
celery = "^5.3.0"
redis = "^5.0.0"
apscheduler = "^3.10.0"  # Lighter alternative to Celery

# Machine Learning (for structure learning)
scikit-learn = "^1.3.0"
transformers = "^4.35.0"  # If using ML for HTML parsing

# Additional
python-dateutil = "^2.8.0"
pytz = "^2023.3"
```

---

## 💡 Key Design Decisions

### 1. **Crawler Architecture**

**Decision**: Use APScheduler for scheduling + asyncio for concurrent crawling
**Rationale**:

- Simpler than Celery for this use case
- Native async support
- Easier to deploy

### 2. **HTML Parsing Strategy**

**Decision**: Hybrid approach (template-based + heuristic fallback)
**Rationale**:

- Template-based for known sources (fast, reliable)
- Heuristic fallback for new/changed sources
- No need for complex ML models initially

### 3. **Causal Analysis Approach**

**Decision**: LLM-based causal reasoning (not statistical causal inference)
**Rationale**:

- Faster to implement
- More interpretable results
- Better suited for explaining "WHY" to end users
- Statistical methods require extensive data and expertise

### 4. **Price Data Storage**

**Decision**: Store all intervals (1m, 5m, 1h, 1d) separately
**Rationale**:

- Different analyses need different granularities
- Avoid resampling complexity
- Easier to query

### 5. **VIP Feature Gating**

**Decision**: Implement at dependency level (not endpoint level)
**Rationale**:

- Consistent across all endpoints
- Easy to modify access rules
- Clear separation of concerns

---

## ✅ Verification Checklist

Before considering the AI service complete, verify:

- [ ] News crawler fetches from at least 3 sources
- [ ] HTML structure learning adapts to 1 website change
- [ ] Sentiment analysis has >80% accuracy on test dataset
- [ ] Price history covers at least 6 months
- [ ] Alignment service calculates correlation metrics
- [ ] Causal analysis generates human-readable explanations
- [ ] VIP users can access advanced features
- [ ] Regular users are blocked from VIP features
- [ ] API documentation is complete
- [ ] All endpoints have proper error handling
- [ ] Background tasks run reliably
- [ ] Database migrations are reversible
- [ ] Unit test coverage >80%
- [ ] Performance: API responds in <500ms
- [ ] Monitoring dashboard shows crawler health

---

## 🎓 References & Resources

### Web Scraping:

- BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/
- Scrapy: https://docs.scrapy.org/
- Playwright: https://playwright.dev/python/

### Causal Analysis:

- DoWhy: https://microsoft.github.io/dowhy/
- CausalML: https://causalml.readthedocs.io/
- "The Book of Why" by Judea Pearl

### OpenAI API:

- API Reference: https://platform.openai.com/docs/api-reference
- Best Practices: https://platform.openai.com/docs/guides/prompt-engineering

### Sentiment Analysis:

- FinBERT: https://github.com/ProsusAI/finBERT
- Financial News Sentiment: https://arxiv.org/abs/1908.10063

---

## 📞 Next Steps

1. **Review this document** with the team
2. **Prioritize missing features** based on business needs
3. **Create detailed task tickets** for implementation
4. **Set up development milestones** (see roadmap)
5. **Begin with Phase 1** (Price History Service)

---

**Document Version**: 1.0
**Last Updated**: December 25, 2025
**Author**: GitHub Copilot AI Assistant
**Status**: Ready for Review
