# 🚀 AI API Integration - Implementation Priority

## 📊 Phân Loại API Endpoints

### ✅ TIER 1: Implement Ngay (No Auth Required)

Những API này **AI Service đã có sẵn**, FE có thể integrate và test ngay lập tức mà không cần authentication.

#### 1. **Sentiment Analysis** ⭐ (Core Feature)

```typescript
// Quick sentiment analysis - Real-time, không lưu DB
POST /api/v1/ai/analyze/quick

// Request
params: {
  text: string,              // Text cần analyze
  use_openai: boolean,       // true = OpenAI, false = keyword fallback
  model_version?: string     // Optional: "gpt-4o-mini" (default)
}

// Response
{
  sentiment_label: "bullish" | "bearish" | "neutral" | "positive" | "negative",
  sentiment_score: number,   // 0.0 - 1.0
  confidence: number,        // 0.0 - 1.0
  model_version: string
}

// Example Usage
const sentiment = await aiApi.post('/ai/analyze/quick', null, {
  params: {
    text: 'Bitcoin surges past $100K on ETF approval!',
    use_openai: true
  }
});
// Result: { sentiment_label: "bullish", sentiment_score: 0.92, confidence: 0.88 }
```

**Use Cases**:

- Real-time sentiment analysis input
- News preview sentiment
- Quick sentiment check
- Testing/demo features

**Implementation Priority**: 🔴 **HIGH** - Core AI feature

---

#### 2. **News Management** (CRUD Operations)

```typescript
// Get news list with pagination
GET /api/v1/news
params: {
  page: number,        // Default: 1
  page_size: number    // Default: 20, Max: 100
}
Response: {
  items: NewsArticle[],
  total: number,
  page: number,
  page_size: number
}

// Get single news article
GET /api/v1/news/{article_id}
Response: NewsArticle

// Create news article (Manual input)
POST /api/v1/news
Body: {
  title: string,           // Required, max 500 chars
  content: string,         // Required
  source: string,          // Required, max 200 chars
  url: string,             // Required, unique
  author?: string,         // Optional
  published_at?: string,   // Optional, ISO datetime
  category?: string        // Optional (e.g., "cryptocurrency", "blockchain")
}
Response: NewsArticle

// Update news article
PATCH /api/v1/news/{article_id}
Body: Partial<NewsArticle>

// Delete news article
DELETE /api/v1/news/{article_id}

// Search news
GET /api/v1/news/search/
params: {
  query: string,       // Search keyword
  page: number,
  page_size: number
}
```

**Use Cases**:

- Display news feed
- Manual news entry (for testing/admin)
- News detail page
- Search functionality

**Implementation Priority**: 🟡 **MEDIUM** - Needed for data display

---

#### 3. **Combined: Analyze News Article**

```typescript
// Analyze a news article that's already in DB and save result
POST /api/v1/ai/analyze/news/{article_id}
params: {
  model_version?: string  // Optional
}
Response: {
  id: number,
  news_article_id: number,
  sentiment_label: string,
  sentiment_score: number,
  confidence: number,
  model_version: string,
  created_at: string,
  updated_at: string
}

// Get latest sentiment for an article
GET /api/v1/ai/news/{article_id}/latest
Response: SentimentAnalysisResponse

// Get all sentiments for an article (history)
GET /api/v1/sentiment/news/{article_id}
Response: SentimentAnalysisResponse[]
```

**Complete Workflow Example**:

```typescript
// Step 1: Create news
const article = await aiApi.post("/news", {
  title: "Bitcoin ETF Approved",
  content: "SEC approves first Bitcoin spot ETF...",
  source: "CoinDesk",
  url: "https://coindesk.com/btc-etf",
});

// Step 2: Analyze sentiment
const sentiment = await aiApi.post(`/ai/analyze/news/${article.id}`);

// Step 3: Display news with sentiment badge
<NewsCard article={article} sentiment={sentiment} />;
```

**Implementation Priority**: 🟡 **MEDIUM** - Good for saved articles

---

#### 4. **Batch Analysis**

```typescript
// Analyze multiple texts at once (max 10)
POST /api/v1/ai/analyze/batch
Body: {
  texts: string[],           // Max 10 texts
  model_version?: string
}
Response: SentimentResult[]

// Example
const results = await aiApi.post('/ai/analyze/batch', {
  texts: [
    'Bitcoin price surges',
    'Market crash imminent',
    'Stable trading expected'
  ]
});
// Returns array of 3 sentiment results
```

**Use Cases**:

- Bulk sentiment analysis
- Compare multiple headlines
- Performance optimization

**Implementation Priority**: 🟢 **LOW** - Nice to have

---

#### 5. **Health Check**

```typescript
// Check if AI service is up and running
GET /api/v1/health
Response: {
  status: "healthy",
  service: "AI Service API",
  version: "1.0.0",
  timestamp: string
}
```

**Implementation Priority**: 🟢 **LOW** - For monitoring

---

### ⚠️ TIER 2: Cần Service Khác (Separate Implementation)

Những features này **AI Service chưa implement**, cần tách ra service riêng hoặc implement sau.

#### ❌ 1. **News Crawler** (Separate Service Recommended)

```typescript
// ❌ CHƯA CÓ TRONG AI SERVICE
// Recommendation: Tạo service riêng hoặc scheduled job

POST / api / v1 / crawler / run; // Trigger manual crawl
GET / api / v1 / crawler / sources; // List configured sources
POST / api / v1 / crawler / sources; // Add new source
GET / api / v1 / crawler / status; // Crawler health

// TODO: Implement in separate service
```

**Why Separate**:

- Crawler cần chạy background jobs
- Different scaling requirements
- Can use scraping-specific tools (Scrapy, Playwright)
- Easier to add rate limiting per source

**Alternative**: Manual news entry + RSS feeds từ service khác

**Priority**: ⏰ **Later** - Can work without it using manual entry

---

#### ❌ 2. **Price History** (Can Use Binance Backend)

```typescript
// ❌ CHƯA CÓ TRONG AI SERVICE
// Recommendation: Use existing binance-backend or separate service

GET / api / v1 / prices / { symbol }; // Get price history
GET / api / v1 / prices / { symbol } / latest; // Get latest price
POST / api / v1 / prices / fetch; // Fetch from Binance

// TODO: Implement OR use existing binance-backend
```

**Why Separate**:

- Price data không thuộc AI domain
- Binance backend đã có WebSocket real-time prices
- Avoid duplication with existing services

**Recommendation**:

```typescript
// Use existing binance-backend service
import { fetchKlines } from "@/lib/services/binance-api";

// Already implemented in FE
const priceData = await fetchKlines("BTCUSDT", "1h");
```

**Priority**: ⏰ **Skip** - Use existing binance-backend

---

#### ❌ 3. **News-Price Alignment** (Future AI Feature)

```typescript
// ❌ CHƯA CÓ - Future implementation in AI service

POST /api/v1/alignment/analyze
Body: {
  news_article_id: number,
  symbol: string,
  time_window_hours: number
}
Response: {
  price_before: number,
  price_after: number,
  price_change_percent: number,
  sentiment_score: number,
  correlation_score: number
}

GET /api/v1/alignment/{symbol}
// Get historical alignments
```

**Why Later**:

- Requires price history integration first
- Complex correlation algorithms
- Not critical for MVP

**Priority**: ⏰ **Phase 2** - After price history

---

#### ❌ 4. **Causal Analysis** (Advanced AI Feature)

```typescript
// ❌ CHƯA CÓ - Advanced feature for later

POST /api/v1/causal/explain
Body: {
  symbol: string,
  timestamp: string,
  price_change: number
}
Response: {
  primary_cause: string,
  confidence: number,
  supporting_evidence: string[],
  explanation: string,        // Human-readable WHY
  causal_strength: "Strong" | "Moderate" | "Weak"
}

GET /api/v1/causal/{symbol}/trend
// Explain trend (UP/DOWN/SIDEWAYS)
```

**Why Later**:

- Requires alignment data first
- Advanced LLM prompting needed
- VIP feature - can monetize later

**Priority**: ⏰ **Phase 3** - VIP feature

---

### 🔐 TIER 3: Requires Authentication (Future)

Hiện tại **TẤT CẢ endpoints đều không cần auth**. Các features sau cần authentication khi implement:

```typescript
// 🔐 Future: VIP-only features
POST /api/v1/causal/*          // Requires VIP
GET  /api/v1/alignment/*       // Requires VIP (or basic for regular)

// 🔐 Future: Admin-only features
POST /api/v1/crawler/sources   // Requires Admin
DELETE /api/v1/news/*          // Requires Admin (or author)
```

**When to implement auth**:

- Phase 2: Basic JWT token verification
- Phase 3: Role-based access (Regular/VIP/Admin)

**Priority**: ⏰ **Phase 2** - After core features working

---

## 🎯 FE Implementation Roadmap

### **Phase 1: Core Features (Week 1-2)** ✅ Start Now

#### Priority 1: Sentiment Analysis Page

```tsx
// Components to create:
1. ✅ SentimentAnalyzer (real-time input)
2. ✅ SentimentBadge (display component)
3. ✅ SentimentHistory (show past analyses)

// Features:
- Real-time text analysis
- Sentiment visualization
- Confidence indicators
```

#### Priority 2: News Feed with Sentiment

```tsx
// Components to create:
1. ✅ NewsFeed (list view)
2. ✅ NewsCard (with sentiment badge)
3. ✅ NewsDetail (single article view)

// Features:
- Paginated news list
- Sentiment badges on each article
- Filter by sentiment
- Search functionality
```

#### Priority 3: News Management (Admin/Testing)

```tsx
// Components to create:
1. ✅ CreateNewsForm (manual entry)
2. ✅ NewsEditor (update article)

// Features:
- Manual news entry for testing
- Automatically analyze after create
- Edit/delete news articles
```

---

### **Phase 2: Integration (Week 3-4)** ⏰ Later

#### If Price History Available:

```tsx
// Components to create:
1. ⏰ PriceChart (use existing binance-backend)
2. ⏰ NewsPriceTimeline (align news with price)
3. ⏰ CorrelationChart (sentiment vs price)
```

#### If Crawler Available:

```tsx
// Components to create:
1. ⏰ AutoNewsRefresh (auto-fetch new articles)
2. ⏰ SourceManager (manage crawler sources)
```

---

### **Phase 3: Advanced (Week 5+)** ⏰ Much Later

```tsx
// VIP Features (requires auth):
1. ⏰ CausalAnalysis (WHY explanations)
2. ⏰ PredictiveInsights (ML predictions)
3. ⏰ CustomAlerts (sentiment-based alerts)
```

---

## 💻 Quick Start Implementation

### 1. Create API Client (`lib/services/ai-api.ts`)

```typescript
import axios from "axios";

const AI_API_URL =
  process.env.NEXT_PUBLIC_AI_API_URL || "http://localhost:8000/api/v1";

export const aiApi = axios.create({
  baseURL: AI_API_URL,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// ===== TIER 1: Implement These First ===== //

// 1. Sentiment Analysis (CORE)
export async function analyzeSentiment(text: string) {
  const { data } = await aiApi.post("/ai/analyze/quick", null, {
    params: { text, use_openai: true },
  });
  return data;
}

// 2. News Management
export async function getNews(page = 1, pageSize = 20) {
  const { data } = await aiApi.get("/news", {
    params: { page, page_size: pageSize },
  });
  return data;
}

export async function getNewsArticle(id: number) {
  const { data } = await aiApi.get(`/news/${id}`);
  return data;
}

export async function createNews(article: CreateNewsRequest) {
  const { data } = await aiApi.post("/news", article);
  return data;
}

export async function searchNews(query: string, page = 1) {
  const { data } = await aiApi.get("/news/search/", {
    params: { query, page, page_size: 20 },
  });
  return data;
}

// 3. Combined: Create + Analyze
export async function createAndAnalyze(newsData: CreateNewsRequest) {
  // Step 1: Create
  const article = await createNews(newsData);

  // Step 2: Analyze
  const { data: sentiment } = await aiApi.post(
    `/ai/analyze/news/${article.id}`
  );

  return { article, sentiment };
}

// 4. Get sentiment for article
export async function getLatestSentiment(articleId: number) {
  const { data } = await aiApi.get(`/ai/news/${articleId}/latest`);
  return data;
}

// 5. Health check
export async function checkHealth() {
  const { data } = await aiApi.get("/health");
  return data;
}

// ===== Types ===== //
export interface CreateNewsRequest {
  title: string;
  content: string;
  source: string;
  url: string;
  author?: string;
  published_at?: string;
  category?: string;
}

export interface NewsArticle extends CreateNewsRequest {
  id: number;
  created_at: string;
  updated_at: string;
}

export interface SentimentResult {
  sentiment_label: string;
  sentiment_score: number;
  confidence: number;
  model_version: string;
}

export interface SentimentAnalysis extends SentimentResult {
  id: number;
  news_article_id: number;
  created_at: string;
  updated_at: string;
}
```

---

### 2. Example Component (`app/(features)/ai-sentiment/page.tsx`)

```tsx
"use client";

import { useState } from "react";
import { analyzeSentiment, type SentimentResult } from "@/lib/services/ai-api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export default function SentimentPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<SentimentResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function analyze() {
    if (!text.trim()) return;

    setLoading(true);
    try {
      const sentiment = await analyzeSentiment(text);
      setResult(sentiment);
    } catch (error) {
      console.error("Analysis failed:", error);
      alert("Failed to analyze sentiment");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <Card>
        <CardHeader>
          <CardTitle>AI Sentiment Analysis</CardTitle>
          <p className="text-sm text-muted-foreground">
            Analyze crypto news sentiment using OpenAI GPT-4o-mini
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Enter crypto news text to analyze sentiment..."
            rows={6}
            className="w-full"
          />

          <Button
            onClick={analyze}
            disabled={loading || !text.trim()}
            className="w-full"
          >
            {loading ? "Analyzing..." : "Analyze Sentiment"}
          </Button>

          {result && (
            <div className="p-4 border rounded-lg bg-muted/50">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl font-bold">
                  {result.sentiment_label.toUpperCase()}
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    result.sentiment_label === "bullish" ||
                    result.sentiment_label === "positive"
                      ? "bg-green-100 text-green-800"
                      : result.sentiment_label === "bearish" ||
                        result.sentiment_label === "negative"
                      ? "bg-red-100 text-red-800"
                      : "bg-gray-100 text-gray-800"
                  }`}
                >
                  Score: {(result.sentiment_score * 100).toFixed(0)}%
                </span>
              </div>

              <div className="space-y-1 text-sm">
                <p>
                  <strong>Confidence:</strong>{" "}
                  {(result.confidence * 100).toFixed(0)}%
                </p>
                <p className="text-muted-foreground">
                  <strong>Model:</strong> {result.model_version}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
```

---

### 3. Example News Feed (`app/(features)/ai-news/page.tsx`)

```tsx
"use client";

import { useEffect, useState } from "react";
import {
  getNews,
  getLatestSentiment,
  type NewsArticle,
  type SentimentAnalysis,
} from "@/lib/services/ai-api";

export default function AINewsPage() {
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [sentiments, setSentiments] = useState<
    Record<number, SentimentAnalysis>
  >({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNews();
  }, []);

  async function loadNews() {
    try {
      const { items } = await getNews(1, 20);
      setNews(items);

      // Load sentiment for each article
      const sentimentPromises = items.map(async (article) => {
        try {
          const sentiment = await getLatestSentiment(article.id);
          return { articleId: article.id, sentiment };
        } catch {
          return null;
        }
      });

      const results = await Promise.all(sentimentPromises);
      const sentimentMap: Record<number, SentimentAnalysis> = {};
      results.forEach((result) => {
        if (result) {
          sentimentMap[result.articleId] = result.sentiment;
        }
      });
      setSentiments(sentimentMap);
    } catch (error) {
      console.error("Failed to load news:", error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div>Loading...</div>;

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">AI News Feed</h1>
      <div className="space-y-4">
        {news.map((article) => {
          const sentiment = sentiments[article.id];
          return (
            <div key={article.id} className="border rounded-lg p-4">
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-bold text-lg">{article.title}</h3>
                {sentiment && (
                  <span
                    className={`px-2 py-1 rounded text-xs ${
                      sentiment.sentiment_label === "bullish"
                        ? "bg-green-100 text-green-800"
                        : sentiment.sentiment_label === "bearish"
                        ? "bg-red-100 text-red-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {sentiment.sentiment_label.toUpperCase()}
                  </span>
                )}
              </div>
              <p className="text-sm text-muted-foreground mb-2">
                {article.source} •{" "}
                {new Date(article.created_at).toLocaleDateString()}
              </p>
              <p className="text-sm">{article.content.substring(0, 200)}...</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

---

## 🧪 Testing Without Auth

All TIER 1 endpoints work without authentication:

```bash
# 1. Test health
curl http://localhost:8000/api/v1/health

# 2. Test sentiment analysis
curl -X POST "http://localhost:8000/api/v1/ai/analyze/quick?text=Bitcoin%20surges&use_openai=true"

# 3. Test create news
curl -X POST http://localhost:8000/api/v1/news \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Article",
    "content": "This is a test",
    "source": "Test",
    "url": "https://example.com/test-123"
  }'

# 4. Test get news
curl http://localhost:8000/api/v1/news?page=1&page_size=10
```

---

## 📝 Environment Setup

```bash
# fe/.env.local
NEXT_PUBLIC_AI_API_URL=http://localhost:8000/api/v1

# For Docker
NEXT_PUBLIC_AI_API_URL=http://ai:8000/api/v1
```

---

## ✅ Implementation Checklist

### Week 1: Core Setup

- [ ] Create `lib/services/ai-api.ts`
- [ ] Add environment variable
- [ ] Test API connection (health check)
- [ ] Create SentimentAnalyzer component
- [ ] Test real-time sentiment analysis

### Week 2: News Features

- [ ] Create news feed page
- [ ] Implement sentiment badges
- [ ] Add manual news creation form
- [ ] Test create + analyze workflow
- [ ] Add search functionality

### Optional (If Time):

- [ ] Batch analysis for multiple texts
- [ ] Sentiment history view
- [ ] News detail page
- [ ] Filter news by sentiment

---

## 🚨 Important Notes

1. **No Authentication Needed**: All TIER 1 APIs work without auth
2. **OpenAI Key Required**: Make sure AI service has valid `OPENAI_API_KEY`
3. **Rate Limits**: OpenAI API has limits, sentiment analysis may be slow
4. **Fallback Mode**: If OpenAI fails, uses keyword-based analysis (less accurate)
5. **CORS**: Make sure AI service allows FE origin

---

## 📞 Quick Links

- **API Docs**: http://localhost:8000/docs
- **Full Integration Guide**: `FE_INTEGRATION_GUIDE.md`
- **AI Status**: `AI_STATUS_SUMMARY.md`

---

**TL;DR**:

- ✅ Use TIER 1 APIs immediately (no auth needed)
- ⏰ TIER 2 features need separate services (skip for now)
- 🔐 TIER 3 needs auth (implement later)
- 🎯 Focus on: Sentiment Analysis + News Feed first!
