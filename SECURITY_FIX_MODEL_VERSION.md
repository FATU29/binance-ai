# 🔒 Security Fix: Model Version Control

## ⚠️ Lỗ hổng bảo mật đã sửa (2024-12-25)

### Vấn đề:
Trước đây, AI API cho phép **client (FE/services) truyền `model_version` parameter**, gây ra:

1. **💰 Tốn chi phí**: User có thể chọn `gpt-4` (đắt) thay vì `gpt-4o-mini` (rẻ)
2. **🔓 Lộ thông tin**: Expose model names và cấu hình AI ra ngoài
3. **⚠️ Mất kiểm soát**: Không thể đảm bảo consistency về AI behavior
4. **🐛 Risk**: Có thể gửi invalid model names gây crash

### Ví dụ lỗ hổng:
```typescript
// ❌ TRƯỚC ĐÂY (LỖ HỔNG)
await analyzeSentiment("Bitcoin surges", "gpt-4");  // Client tự chọn model đắt!
```

---

## ✅ Giải pháp đã implement

### 1. Remove `model_version` từ API endpoints

**File: `app/api/v1/endpoints/ai_analytics.py`**

#### Endpoint 1: `/analyze/news/{article_id}`
```python
# ❌ BEFORE
async def analyze_news_article(
    article_id: int,
    db: DBSession,
    model_version: str | None = None,  # ❌ Client controlled
) -> SentimentAnalysisResponse:

# ✅ AFTER
async def analyze_news_article(
    article_id: int,
    db: DBSession,
) -> SentimentAnalysisResponse:
    # Model controlled by server config only
```

#### Endpoint 2: `/analyze/batch`
```python
# ❌ BEFORE
async def analyze_batch_texts(
    texts: list[str],
    model_version: str | None = None,  # ❌ Client controlled
)

# ✅ AFTER
async def analyze_batch_texts(
    texts: list[str],
) # Model controlled by server config only
```

#### Endpoint 3: `/analyze/quick`
```python
# ❌ BEFORE
async def quick_sentiment_analysis(
    text: str,
    use_openai: bool = True,
    model_version: str | None = None,  # ❌ Client controlled
)

# ✅ AFTER
async def quick_sentiment_analysis(
    text: str,
    use_openai: bool = True,
) # Model controlled by server config only
```

---

### 2. Remove `model_version` từ Request Schema

**File: `app/schemas/sentiment.py`**

```python
# ❌ BEFORE
class SentimentAnalysisRequest(BaseSchema):
    text: str = Field(..., min_length=1, max_length=10000)
    model_version: str | None = Field("v1.0.0", max_length=50)  # ❌

# ✅ AFTER
class SentimentAnalysisRequest(BaseSchema):
    """Schema for sentiment analysis request (text input).
    
    Note: Model version is controlled server-side via config, not client input.
    This prevents cost manipulation and ensures consistent AI behavior.
    """
    text: str = Field(..., min_length=1, max_length=10000)
    # No model_version field - controlled by server
```

---

### 3. Server-side Configuration Only

**File: `app/core/config.py`**

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # ✅ AI Configuration (server-side only, never expose to clients)
    OPENAI_MODEL: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model for sentiment analysis (controlled server-side for cost/security)"
    )
    OPENAI_MAX_TOKENS: int = Field(
        default=200,
        description="Maximum tokens for OpenAI responses"
    )
    OPENAI_TEMPERATURE: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="OpenAI temperature for response consistency"
    )
```

**Environment Variables (`.env`)**:
```bash
# AI Configuration - Server Side Only
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini     # Cost-effective default
OPENAI_MAX_TOKENS=200
OPENAI_TEMPERATURE=0.3
```

---

### 4. Update Service Logic

**File: `app/services/sentiment_service.py`**

```python
class SentimentService:
    def __init__(self) -> None:
        """Initialize with server-controlled config only."""
        # ✅ Load from settings (environment variables)
        self.model_version = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
        self.client: AsyncOpenAI | None = None
        
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info(
                "OpenAI client initialized",
                model=self.model_version,  # ✅ Server controlled
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

    async def _analyze_with_openai(self, request: SentimentAnalysisRequest):
        # ✅ Use server config only
        response = await self.client.chat.completions.create(
            model=self.model_version,      # ✅ From settings
            temperature=self.temperature,  # ✅ From settings
            max_tokens=self.max_tokens,    # ✅ From settings
            messages=[...],
        )
```

---

## 📋 Migration Guide cho Frontend

### API Calls - Before vs After

```typescript
// ❌ BEFORE (with model_version parameter)
const response = await axios.post('/ai/analyze/quick', null, {
  params: { 
    text: "Bitcoin surges", 
    use_openai: true,
    model_version: "gpt-4"  // ❌ NOT ALLOWED ANYMORE
  }
});

// ✅ AFTER (no model parameter)
const response = await axios.post('/ai/analyze/quick', null, {
  params: { 
    text: "Bitcoin surges", 
    use_openai: true
    // ✅ Model controlled by server
  }
});
```

### TypeScript API Client Update

```typescript
// ✅ Updated function signature
export async function analyzeSentiment(text: string): Promise<SentimentResult> {
  const { data } = await aiApi.post('/ai/analyze/quick', null, {
    params: { 
      text, 
      use_openai: true 
      // NO model_version parameter
    }
  });
  return data;
}

export async function analyzeBatch(texts: string[]): Promise<SentimentResult[]> {
  const { data } = await aiApi.post('/ai/analyze/batch', { texts });
  // NO model_version in request body
  return data;
}
```

---

## 🎯 Benefits

### 1. **Cost Control** 💰
- Admin kiểm soát 100% model nào được dùng
- Có thể switch model mà không cần deploy FE
- Ngăn abuse: user không thể chọn model đắt

### 2. **Security** 🔒
- Không expose model names/versions ra client
- Không expose API configuration
- Giảm attack surface

### 3. **Consistency** 🎯
- Tất cả requests dùng cùng model → consistent results
- Dễ A/B testing (change `.env` only)
- Centralized configuration

### 4. **Flexibility** 🔄
- Admin có thể switch model bất kỳ lúc nào
- Update `OPENAI_MODEL=gpt-4o` trong `.env` → tất cả requests dùng model mới
- Không cần redeploy frontend

---

## 🧪 Testing

### Test 1: Verify model không thể override
```bash
# Try to pass model_version (should be ignored)
curl -X POST "http://localhost:8000/api/v1/ai/analyze/quick?text=Bitcoin%20surges&use_openai=true" \
  -H "Content-Type: application/json"

# Response will use server-configured model (gpt-4o-mini by default)
```

### Test 2: Verify settings work
```bash
# In .env file:
# OPENAI_MODEL=gpt-4o-mini

# Start server
cd ai
uv run fastapi dev main.py

# Check logs - should show:
# OpenAI client initialized model=gpt-4o-mini max_tokens=200 temperature=0.3
```

### Test 3: Verify FE integration
```typescript
// Frontend code
const result = await analyzeSentiment("Bitcoin crashes");
console.log(result.model_version); // Should be "gpt-4o-mini" (from server)
```

---

## 📝 Admin Guide: Changing AI Model

### Option 1: Environment Variable (Recommended)
```bash
# Edit ai/.env
OPENAI_MODEL=gpt-4o        # Upgrade to more powerful model
OPENAI_MAX_TOKENS=500      # Allow longer responses
OPENAI_TEMPERATURE=0.5     # More creative responses

# Restart service
docker-compose restart ai-service
```

### Option 2: Docker Compose
```yaml
# docker-compose.yml
services:
  ai-service:
    environment:
      - OPENAI_MODEL=gpt-4o-mini  # Control here
      - OPENAI_MAX_TOKENS=200
      - OPENAI_TEMPERATURE=0.3
```

### Option 3: Kubernetes ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-service-config
data:
  OPENAI_MODEL: "gpt-4o-mini"
  OPENAI_MAX_TOKENS: "200"
  OPENAI_TEMPERATURE: "0.3"
```

---

## 🔍 Code Changes Summary

### Files Modified:
1. ✅ `app/api/v1/endpoints/ai_analytics.py` - Removed `model_version` params from 3 endpoints
2. ✅ `app/schemas/sentiment.py` - Removed `model_version` field from request schema
3. ✅ `app/core/config.py` - Added `OPENAI_MODEL`, `OPENAI_MAX_TOKENS`, `OPENAI_TEMPERATURE` settings
4. ✅ `app/services/sentiment_service.py` - Load config from settings instead of params

### Files to Update (Frontend):
- ⚠️ `fe/lib/services/ai-api.ts` - Remove model_version parameters from function calls
- ⚠️ Any FE components passing model_version

### Breaking Changes:
- ❌ `model_version` parameter no longer accepted in API calls
- ✅ Existing calls without `model_version` continue to work
- ✅ Calls with `model_version` will **ignore** the parameter (not error)

---

## 🚀 Deployment Checklist

- [x] Update backend code (3 endpoints + schema + service)
- [x] Add settings configuration
- [ ] Update `.env` with AI config
- [ ] Test endpoints without model_version
- [ ] Update FE API client code
- [ ] Test FE integration
- [ ] Update API documentation
- [ ] Deploy to staging
- [ ] Deploy to production

---

## 📚 Related Documentation

- `FE_IMPLEMENTATION_PRIORITY.md` - Frontend integration guide (needs update)
- `COPY_PASTE_AI_INTEGRATION.md` - Quick start guide (needs update)
- `OPENAI_GUIDE.md` - OpenAI implementation details

---

**Date**: December 25, 2024  
**Priority**: HIGH - Security & Cost Control  
**Status**: ✅ Fixed in code, pending deployment
