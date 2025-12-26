# AI Service - Frontend Integration Guide

## 📋 Tổng Quan

Document này hướng dẫn Frontend (Next.js) tích hợp với AI Service API để sử dụng các tính năng:

- ✅ **Sentiment Analysis**: Phân tích cảm xúc tin tức bằng AI
- ✅ **News Management**: Quản lý tin tức tài chính
- ⚠️ **Price History**: API sẵn sàng nhưng chưa có data
- ⚠️ **News-Price Alignment**: Đang phát triển
- ⚠️ **Causal Analysis**: Đang phát triển

---

## 🔗 Base URL

```typescript
// Development
const AI_API_BASE_URL = "http://localhost:8000/api/v1";

// Production (Docker)
const AI_API_BASE_URL = "http://ai:8000/api/v1";
```

---

## 🚀 Quick Start

### 1. Cài Đặt Dependencies

```bash
cd fe
npm install axios
# hoặc
npm install ky
```

### 2. Tạo AI API Client

Tạo file `lib/services/ai-api.ts`:

```typescript
import axios, { AxiosInstance } from "axios";

// Base configuration
const AI_API_BASE_URL =
  process.env.NEXT_PUBLIC_AI_API_URL || "http://localhost:8000/api/v1";

// Create axios instance
export const aiApiClient: AxiosInstance = axios.create({
  baseURL: AI_API_BASE_URL,
  timeout: 30000, // 30 seconds for AI operations
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor (add auth token if needed)
aiApiClient.interceptors.request.use(
  (config) => {
    // Add auth token from localStorage/cookies
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor (handle errors)
aiApiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("AI API Error:", error.response?.data || error.message);
    return Promise.reject(error);
  }
);
```

---

## 📚 API Endpoints & Usage

### 1. Health Check

Kiểm tra trạng thái AI service.

#### Endpoint

```
GET /health
```

#### TypeScript Example

```typescript
export async function checkAIHealth() {
  const response = await aiApiClient.get("/health");
  return response.data;
}

// Response Type
interface HealthResponse {
  status: string; // "healthy"
  service: string; // "AI Service API"
  version: string; // "1.0.0"
  timestamp: string; // ISO datetime
}
```

#### Usage in Component

```tsx
"use client";

import { useEffect, useState } from "react";
import { checkAIHealth } from "@/lib/services/ai-api";

export function AIStatusIndicator() {
  const [status, setStatus] = useState<"online" | "offline">("offline");

  useEffect(() => {
    checkAIHealth()
      .then(() => setStatus("online"))
      .catch(() => setStatus("offline"));
  }, []);

  return (
    <div className={status === "online" ? "text-green-500" : "text-red-500"}>
      AI Service: {status}
    </div>
  );
}
```

---

### 2. News Articles Management

#### 2.1 Get News List (Paginated)

```typescript
interface NewsArticle {
  id: number;
  title: string;
  content: string;
  source: string;
  url: string;
  author: string | null;
  published_at: string | null; // ISO datetime
  category: string | null;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

interface NewsListResponse {
  items: NewsArticle[];
  total: number;
  page: number;
  page_size: number;
}

export async function getNewsList(
  page = 1,
  pageSize = 20
): Promise<NewsListResponse> {
  const response = await aiApiClient.get("/news", {
    params: { page, page_size: pageSize },
  });
  return response.data;
}
```

**Usage:**

```tsx
"use client";

import { useEffect, useState } from "react";
import { getNewsList, NewsArticle } from "@/lib/services/ai-api";

export function NewsList() {
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  useEffect(() => {
    setLoading(true);
    getNewsList(page, 20)
      .then((data) => {
        setNews(data.items);
      })
      .finally(() => setLoading(false));
  }, [page]);

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      {news.map((article) => (
        <div key={article.id} className="border p-4 mb-2">
          <h3 className="font-bold">{article.title}</h3>
          <p className="text-sm text-gray-600">{article.source}</p>
          <p>{article.content.substring(0, 200)}...</p>
        </div>
      ))}
      <button onClick={() => setPage(page - 1)} disabled={page === 1}>
        Previous
      </button>
      <button onClick={() => setPage(page + 1)}>Next</button>
    </div>
  );
}
```

#### 2.2 Get Single News Article

```typescript
export async function getNewsArticle(articleId: number): Promise<NewsArticle> {
  const response = await aiApiClient.get(`/news/${articleId}`);
  return response.data;
}
```

#### 2.3 Create News Article

```typescript
interface CreateNewsArticle {
  title: string;
  content: string;
  source: string;
  url: string;
  author?: string | null;
  published_at?: string | null; // ISO datetime
  category?: string | null;
}

export async function createNewsArticle(
  article: CreateNewsArticle
): Promise<NewsArticle> {
  const response = await aiApiClient.post("/news", article);
  return response.data;
}
```

**Usage:**

```tsx
async function handleCreateNews() {
  try {
    const newArticle = await createNewsArticle({
      title: "Bitcoin Breaks $100K",
      content: "Bitcoin has reached a new all-time high...",
      source: "CoinDesk",
      url: "https://coindesk.com/bitcoin-100k",
      category: "cryptocurrency",
      published_at: new Date().toISOString(),
    });
    console.log("Created:", newArticle);
  } catch (error) {
    console.error("Failed to create article:", error);
  }
}
```

#### 2.4 Search News

```typescript
export async function searchNews(
  query: string,
  page = 1,
  pageSize = 20
): Promise<NewsListResponse> {
  const response = await aiApiClient.get("/news/search/", {
    params: { query, page, page_size: pageSize },
  });
  return response.data;
}
```

**Usage:**

```tsx
const [searchQuery, setSearchQuery] = useState("");
const [results, setResults] = useState<NewsArticle[]>([]);

async function handleSearch() {
  const data = await searchNews(searchQuery);
  setResults(data.items);
}

return (
  <div>
    <input
      value={searchQuery}
      onChange={(e) => setSearchQuery(e.target.value)}
      placeholder="Search news..."
    />
    <button onClick={handleSearch}>Search</button>
    {/* Display results */}
  </div>
);
```

---

### 3. Sentiment Analysis ⭐ (AI Feature)

#### 3.1 Quick Sentiment Analysis (No Database)

**Endpoint:** `POST /ai/analyze/quick`

Phân tích nhanh một đoạn text mà không lưu vào database. Tốt nhất cho real-time analysis.

```typescript
interface SentimentAnalysisRequest {
  text: string;
  model_version?: string; // Optional: "gpt-4o-mini" (default) or "gpt-4o"
}

interface SentimentAnalysisResult {
  sentiment_label: string; // "bullish", "bearish", "neutral", "positive", "negative"
  sentiment_score: number; // 0.0 to 1.0
  confidence: number; // 0.0 to 1.0
  model_version: string; // "gpt-4o-mini" or "keyword-fallback-v1.0.0"
}

export async function analyzeTextSentiment(
  text: string,
  useOpenAI = true,
  modelVersion?: string
): Promise<SentimentAnalysisResult> {
  const response = await aiApiClient.post("/ai/analyze/quick", null, {
    params: {
      text,
      use_openai: useOpenAI,
      model_version: modelVersion,
    },
  });
  return response.data;
}
```

**Usage in Real-Time Input:**

```tsx
"use client";

import { useState } from "react";
import { analyzeTextSentiment } from "@/lib/services/ai-api";

export function SentimentAnalyzer() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function analyze() {
    if (!text.trim()) return;

    setLoading(true);
    try {
      const sentiment = await analyzeTextSentiment(text);
      setResult(sentiment);
    } catch (error) {
      console.error("Analysis failed:", error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Enter text to analyze sentiment..."
        className="w-full p-2 border rounded"
        rows={4}
      />
      <button
        onClick={analyze}
        disabled={loading}
        className="px-4 py-2 bg-blue-500 text-white rounded"
      >
        {loading ? "Analyzing..." : "Analyze Sentiment"}
      </button>

      {result && (
        <div className="p-4 border rounded">
          <h3 className="font-bold">Results:</h3>
          <p>
            Sentiment:{" "}
            <span className={getSentimentColor(result.sentiment_label)}>
              {result.sentiment_label.toUpperCase()}
            </span>
          </p>
          <p>Score: {result.sentiment_score.toFixed(2)}</p>
          <p>Confidence: {(result.confidence * 100).toFixed(0)}%</p>
          <p className="text-sm text-gray-600">Model: {result.model_version}</p>
        </div>
      )}
    </div>
  );
}

function getSentimentColor(label: string) {
  switch (label) {
    case "bullish":
    case "positive":
      return "text-green-600 font-bold";
    case "bearish":
    case "negative":
      return "text-red-600 font-bold";
    default:
      return "text-gray-600 font-bold";
  }
}
```

#### 3.2 Analyze News Article and Save

**Endpoint:** `POST /ai/analyze/news/{article_id}`

Phân tích sentiment của một news article đã có trong database và lưu kết quả.

```typescript
interface SentimentAnalysisResponse {
  id: number;
  news_article_id: number;
  sentiment_label: string;
  sentiment_score: number;
  confidence: number;
  model_version: string;
  analysis_metadata: string | null; // JSON string
  created_at: string;
  updated_at: string;
}

export async function analyzeNewsArticle(
  articleId: number,
  modelVersion?: string
): Promise<SentimentAnalysisResponse> {
  const response = await aiApiClient.post(
    `/ai/analyze/news/${articleId}`,
    null,
    { params: { model_version: modelVersion } }
  );
  return response.data;
}
```

**Usage:**

```tsx
async function handleAnalyzeArticle(articleId: number) {
  try {
    const analysis = await analyzeNewsArticle(articleId);
    console.log("Analysis saved:", analysis);
    // Update UI with analysis results
  } catch (error) {
    console.error("Analysis failed:", error);
  }
}
```

#### 3.3 Batch Analysis

**Endpoint:** `POST /ai/analyze/batch`

Phân tích nhiều text cùng lúc (max 10 texts).

```typescript
export async function analyzeBatchTexts(
  texts: string[],
  modelVersion?: string
): Promise<SentimentAnalysisResult[]> {
  if (texts.length > 10) {
    throw new Error("Maximum 10 texts allowed per batch");
  }

  const response = await aiApiClient.post("/ai/analyze/batch", {
    texts,
    model_version: modelVersion,
  });
  return response.data;
}
```

**Usage:**

```tsx
async function analyzeBatch() {
  const texts = [
    "Bitcoin price surges to new high!",
    "Market crash imminent, experts warn",
    "Stable prices expected this week",
  ];

  const results = await analyzeBatchTexts(texts);
  results.forEach((result, index) => {
    console.log(`Text ${index + 1}:`, result.sentiment_label);
  });
}
```

#### 3.4 Get Latest Sentiment for Article

**Endpoint:** `GET /ai/news/{article_id}/latest`

Lấy sentiment analysis mới nhất cho một article.

```typescript
export async function getLatestSentimentForArticle(
  articleId: number
): Promise<SentimentAnalysisResponse> {
  const response = await aiApiClient.get(`/ai/news/${articleId}/latest`);
  return response.data;
}
```

#### 3.5 Get All Sentiments for Article

**Endpoint:** `GET /sentiment/news/{article_id}`

Lấy tất cả sentiment analyses cho một article (có thể có nhiều nếu analyze nhiều lần).

```typescript
export async function getSentimentsForArticle(
  articleId: number
): Promise<SentimentAnalysisResponse[]> {
  const response = await aiApiClient.get(`/sentiment/news/${articleId}`);
  return response.data;
}
```

---

### 4. Complete Workflow Example

Workflow hoàn chỉnh: Tạo news → Analyze sentiment → Display results

```tsx
"use client";

import { useState } from "react";
import {
  createNewsArticle,
  analyzeNewsArticle,
  type NewsArticle,
  type SentimentAnalysisResponse,
} from "@/lib/services/ai-api";

export function NewsWithSentiment() {
  const [newsData, setNewsData] = useState({
    title: "",
    content: "",
    source: "",
    url: "",
  });
  const [createdArticle, setCreatedArticle] = useState<NewsArticle | null>(
    null
  );
  const [sentiment, setSentiment] = useState<SentimentAnalysisResponse | null>(
    null
  );
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    try {
      // Step 1: Create news article
      const article = await createNewsArticle({
        ...newsData,
        published_at: new Date().toISOString(),
        category: "cryptocurrency",
      });
      setCreatedArticle(article);
      console.log("✅ Article created:", article.id);

      // Step 2: Analyze sentiment
      const analysis = await analyzeNewsArticle(article.id);
      setSentiment(analysis);
      console.log("✅ Sentiment analyzed:", analysis.sentiment_label);
    } catch (error) {
      console.error("❌ Error:", error);
      alert("Failed to process news article");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">Add News & Analyze Sentiment</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="text"
          placeholder="Title"
          value={newsData.title}
          onChange={(e) => setNewsData({ ...newsData, title: e.target.value })}
          required
          className="w-full p-2 border rounded"
        />
        <textarea
          placeholder="Content"
          value={newsData.content}
          onChange={(e) =>
            setNewsData({ ...newsData, content: e.target.value })
          }
          required
          rows={6}
          className="w-full p-2 border rounded"
        />
        <input
          type="text"
          placeholder="Source (e.g., CoinDesk)"
          value={newsData.source}
          onChange={(e) => setNewsData({ ...newsData, source: e.target.value })}
          required
          className="w-full p-2 border rounded"
        />
        <input
          type="url"
          placeholder="URL"
          value={newsData.url}
          onChange={(e) => setNewsData({ ...newsData, url: e.target.value })}
          required
          className="w-full p-2 border rounded"
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Processing..." : "Create & Analyze"}
        </button>
      </form>

      {/* Results */}
      {createdArticle && sentiment && (
        <div className="mt-6 p-4 border rounded bg-gray-50">
          <h3 className="font-bold text-lg mb-2">✅ Analysis Complete</h3>
          <div className="space-y-2">
            <p>
              <strong>Article ID:</strong> {createdArticle.id}
            </p>
            <p>
              <strong>Sentiment:</strong>{" "}
              <span
                className={`font-bold ${
                  sentiment.sentiment_label.includes("bullish") ||
                  sentiment.sentiment_label === "positive"
                    ? "text-green-600"
                    : sentiment.sentiment_label.includes("bearish") ||
                      sentiment.sentiment_label === "negative"
                    ? "text-red-600"
                    : "text-gray-600"
                }`}
              >
                {sentiment.sentiment_label.toUpperCase()}
              </span>
            </p>
            <p>
              <strong>Score:</strong> {sentiment.sentiment_score.toFixed(2)}
            </p>
            <p>
              <strong>Confidence:</strong>{" "}
              {(sentiment.confidence * 100).toFixed(0)}%
            </p>
            <p className="text-sm text-gray-600">
              <strong>Model:</strong> {sentiment.model_version}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 🎨 UI Components Recommendations

### Sentiment Badge Component

```tsx
interface SentimentBadgeProps {
  label: string;
  score: number;
  confidence: number;
}

export function SentimentBadge({
  label,
  score,
  confidence,
}: SentimentBadgeProps) {
  const getColor = () => {
    switch (label.toLowerCase()) {
      case "bullish":
      case "positive":
        return "bg-green-100 text-green-800 border-green-300";
      case "bearish":
      case "negative":
        return "bg-red-100 text-red-800 border-red-300";
      default:
        return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border ${getColor()}`}
    >
      <span className="font-semibold">{label.toUpperCase()}</span>
      <span className="text-xs">
        {(score * 100).toFixed(0)}% ({(confidence * 100).toFixed(0)}% conf)
      </span>
    </div>
  );
}
```

### News Card with Sentiment

```tsx
import { SentimentBadge } from "./SentimentBadge";

interface NewsCardProps {
  article: NewsArticle;
  sentiment?: SentimentAnalysisResponse;
  onAnalyze?: () => void;
}

export function NewsCard({ article, sentiment, onAnalyze }: NewsCardProps) {
  return (
    <div className="border rounded-lg p-4 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-bold text-lg">{article.title}</h3>
        {sentiment && (
          <SentimentBadge
            label={sentiment.sentiment_label}
            score={sentiment.sentiment_score}
            confidence={sentiment.confidence}
          />
        )}
      </div>

      <p className="text-sm text-gray-600 mb-2">
        {article.source} •{" "}
        {new Date(
          article.published_at || article.created_at
        ).toLocaleDateString()}
      </p>

      <p className="text-gray-700 mb-3">
        {article.content.substring(0, 200)}...
      </p>

      <div className="flex items-center gap-2">
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline text-sm"
        >
          Read Full Article →
        </a>
        {!sentiment && onAnalyze && (
          <button
            onClick={onAnalyze}
            className="ml-auto px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700"
          >
            Analyze Sentiment
          </button>
        )}
      </div>
    </div>
  );
}
```

---

## 🔐 Authentication & Authorization

Hiện tại AI Service **chưa implement** authentication đầy đủ. Để tích hợp:

### Option 1: Add JWT Token

Thêm token vào headers trong `aiApiClient`:

```typescript
aiApiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Option 2: VIP Feature Gating (Future)

Khi AI service implement VIP features:

```typescript
// Check if user has VIP access before calling advanced endpoints
async function analyzeCausalRelationship(articleId: number) {
  const user = await getCurrentUser();

  if (!user.isVIP) {
    throw new Error("VIP subscription required for causal analysis");
  }

  // Call VIP endpoint
  const response = await aiApiClient.post(`/ai/causal/analyze/${articleId}`);
  return response.data;
}
```

---

## ⚠️ Features Status & Limitations

### ✅ Fully Available:

- News CRUD operations
- Sentiment analysis (OpenAI GPT-4o-mini)
- Real-time sentiment analysis
- Batch sentiment analysis

### ⚠️ Partially Available:

- Price history (API ready, no data yet)
- Binance integration (structure exists, empty)

### ❌ Not Available Yet:

- News crawler (not implemented)
- Multi-source news fetching
- News-price alignment analysis
- Causal analysis (why prices move)
- VIP feature gating

---

## 🚨 Error Handling

Recommended error handling pattern:

```typescript
import { AxiosError } from "axios";

async function safeAPICall<T>(
  apiCall: () => Promise<T>
): Promise<{ data?: T; error?: string }> {
  try {
    const data = await apiCall();
    return { data };
  } catch (error) {
    if (error instanceof AxiosError) {
      const message = error.response?.data?.detail || error.message;
      console.error("API Error:", message);
      return { error: message };
    }
    return { error: "Unknown error occurred" };
  }
}

// Usage
const { data, error } = await safeAPICall(() =>
  analyzeTextSentiment("Bitcoin to the moon!")
);

if (error) {
  toast.error(error);
  return;
}

console.log("Success:", data);
```

---

## 🧪 Testing API

### Using curl:

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Quick sentiment analysis
curl -X POST "http://localhost:8000/api/v1/ai/analyze/quick?text=Bitcoin%20price%20surges&use_openai=true"

# Create news article
curl -X POST "http://localhost:8000/api/v1/news" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Article",
    "content": "This is a test article about crypto.",
    "source": "Test Source",
    "url": "https://example.com/test"
  }'

# Get news list
curl "http://localhost:8000/api/v1/news?page=1&page_size=10"
```

### Using Postman/Insomnia:

Import OpenAPI docs from: `http://localhost:8000/docs` (Swagger UI)

---

## 📦 Complete API Client Export

Tạo file `lib/services/ai-api.ts` với tất cả functions:

```typescript
// lib/services/ai-api.ts
import axios, { AxiosInstance } from "axios";

const AI_API_BASE_URL =
  process.env.NEXT_PUBLIC_AI_API_URL || "http://localhost:8000/api/v1";

export const aiApiClient: AxiosInstance = axios.create({
  baseURL: AI_API_BASE_URL,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// Types
export interface NewsArticle {
  id: number;
  title: string;
  content: string;
  source: string;
  url: string;
  author: string | null;
  published_at: string | null;
  category: string | null;
  created_at: string;
  updated_at: string;
}

export interface NewsListResponse {
  items: NewsArticle[];
  total: number;
  page: number;
  page_size: number;
}

export interface SentimentAnalysisResult {
  sentiment_label: string;
  sentiment_score: number;
  confidence: number;
  model_version: string;
}

export interface SentimentAnalysisResponse extends SentimentAnalysisResult {
  id: number;
  news_article_id: number;
  analysis_metadata: string | null;
  created_at: string;
  updated_at: string;
}

// Health
export async function checkAIHealth() {
  const response = await aiApiClient.get("/health");
  return response.data;
}

// News
export async function getNewsList(
  page = 1,
  pageSize = 20
): Promise<NewsListResponse> {
  const response = await aiApiClient.get("/news", {
    params: { page, page_size: pageSize },
  });
  return response.data;
}

export async function getNewsArticle(articleId: number): Promise<NewsArticle> {
  const response = await aiApiClient.get(`/news/${articleId}`);
  return response.data;
}

export async function createNewsArticle(article: {
  title: string;
  content: string;
  source: string;
  url: string;
  author?: string | null;
  published_at?: string | null;
  category?: string | null;
}): Promise<NewsArticle> {
  const response = await aiApiClient.post("/news", article);
  return response.data;
}

export async function searchNews(
  query: string,
  page = 1,
  pageSize = 20
): Promise<NewsListResponse> {
  const response = await aiApiClient.get("/news/search/", {
    params: { query, page, page_size: pageSize },
  });
  return response.data;
}

// Sentiment Analysis
export async function analyzeTextSentiment(
  text: string,
  useOpenAI = true,
  modelVersion?: string
): Promise<SentimentAnalysisResult> {
  const response = await aiApiClient.post("/ai/analyze/quick", null, {
    params: { text, use_openai: useOpenAI, model_version: modelVersion },
  });
  return response.data;
}

export async function analyzeNewsArticle(
  articleId: number,
  modelVersion?: string
): Promise<SentimentAnalysisResponse> {
  const response = await aiApiClient.post(
    `/ai/analyze/news/${articleId}`,
    null,
    {
      params: { model_version: modelVersion },
    }
  );
  return response.data;
}

export async function analyzeBatchTexts(
  texts: string[],
  modelVersion?: string
): Promise<SentimentAnalysisResult[]> {
  const response = await aiApiClient.post("/ai/analyze/batch", {
    texts,
    model_version: modelVersion,
  });
  return response.data;
}

export async function getLatestSentimentForArticle(
  articleId: number
): Promise<SentimentAnalysisResponse> {
  const response = await aiApiClient.get(`/ai/news/${articleId}/latest`);
  return response.data;
}

export async function getSentimentsForArticle(
  articleId: number
): Promise<SentimentAnalysisResponse[]> {
  const response = await aiApiClient.get(`/sentiment/news/${articleId}`);
  return response.data;
}
```

---

## 🎯 Next Steps

1. **Copy** `ai-api.ts` vào `fe/lib/services/`
2. **Add** environment variable trong `.env.local`:
   ```
   NEXT_PUBLIC_AI_API_URL=http://localhost:8000/api/v1
   ```
3. **Test** API connection với health check
4. **Implement** news listing page
5. **Add** sentiment analysis features

---

## 📞 Support

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **Redoc**: http://localhost:8000/redoc

---

**Last Updated**: December 25, 2025
**Version**: 1.0
**Status**: Production Ready ✅
