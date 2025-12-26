# AI Service API - Quick Start Guide

## 🚀 Quick Integration (5 phút)

### 1. Setup API Client

Tạo file `fe/lib/services/ai-api.ts`:

```typescript
import axios from "axios";

export const aiApi = axios.create({
  baseURL: "http://localhost:8000/api/v1",
  timeout: 30000,
});

// Types
export interface NewsArticle {
  id: number;
  title: string;
  content: string;
  source: string;
  url: string;
  published_at: string | null;
  category: string | null;
}

export interface SentimentResult {
  sentiment_label: string; // "bullish", "bearish", "neutral"
  sentiment_score: number; // 0.0 to 1.0
  confidence: number; // 0.0 to 1.0
}
```

### 2. Essential API Calls

#### Check Health

```typescript
export async function checkHealth() {
  const { data } = await aiApi.get("/health");
  return data;
}
```

#### Get News List

```typescript
export async function getNews(page = 1) {
  const { data } = await aiApi.get("/news", {
    params: { page, page_size: 20 },
  });
  return data; // { items: NewsArticle[], total: number, ... }
}
```

#### Analyze Sentiment (Quick)

```typescript
export async function analyzeSentiment(text: string): Promise<SentimentResult> {
  const { data } = await aiApi.post("/ai/analyze/quick", null, {
    params: { text, use_openai: true },
  });
  return data;
}
```

#### Create News & Analyze

```typescript
export async function createAndAnalyzeNews(newsData: {
  title: string;
  content: string;
  source: string;
  url: string;
}) {
  // Step 1: Create news
  const { data: article } = await aiApi.post("/news", newsData);

  // Step 2: Analyze sentiment
  const { data: sentiment } = await aiApi.post(
    `/ai/analyze/news/${article.id}`
  );

  return { article, sentiment };
}
```

### 3. Example Component

```tsx
"use client";

import { useState } from "react";
import { analyzeSentiment, type SentimentResult } from "@/lib/services/ai-api";

export function QuickSentimentAnalyzer() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<SentimentResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function analyze() {
    setLoading(true);
    try {
      const sentiment = await analyzeSentiment(text);
      setResult(sentiment);
    } catch (error) {
      alert("Error: " + error.message);
    }
    setLoading(false);
  }

  return (
    <div className="p-4 space-y-4">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Enter crypto news text..."
        className="w-full p-2 border rounded"
        rows={4}
      />

      <button
        onClick={analyze}
        disabled={loading || !text}
        className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
      >
        {loading ? "Analyzing..." : "Analyze Sentiment"}
      </button>

      {result && (
        <div className="p-4 border rounded bg-gray-50">
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold">
              {result.sentiment_label.toUpperCase()}
            </span>
            <span
              className={`px-2 py-1 rounded ${
                result.sentiment_label === "bullish" ||
                result.sentiment_label === "positive"
                  ? "bg-green-100 text-green-800"
                  : result.sentiment_label === "bearish" ||
                    result.sentiment_label === "negative"
                  ? "bg-red-100 text-red-800"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              {(result.sentiment_score * 100).toFixed(0)}%
            </span>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Confidence: {(result.confidence * 100).toFixed(0)}%
          </p>
        </div>
      )}
    </div>
  );
}
```

## 📋 Available Endpoints

### News Management

```typescript
GET    /news                    // List news (paginated)
GET    /news/{id}               // Get single news
POST   /news                    // Create news
GET    /news/search/?query={}   // Search news
```

### Sentiment Analysis (AI)

```typescript
POST / ai / analyze / quick; // Quick analysis (no DB save)
POST / ai / analyze / news / { article_id }; // Analyze & save article
POST / ai / analyze / batch; // Batch analysis (max 10)
GET / ai / news / { article_id } / latest; // Get latest sentiment
```

### Health

```typescript
GET / health; // Check API status
```

## 🎯 Common Use Cases

### 1. Display News Feed with Sentiment

```typescript
async function fetchNewsWithSentiment() {
  const newsData = await getNews(1);

  // For each news item, try to get sentiment
  const newsWithSentiment = await Promise.all(
    newsData.items.map(async (article) => {
      try {
        const sentiment = await aiApi.get(`/ai/news/${article.id}/latest`);
        return { ...article, sentiment: sentiment.data };
      } catch {
        return article; // No sentiment available
      }
    })
  );

  return newsWithSentiment;
}
```

### 2. Real-time Sentiment Input

```typescript
// Use debounce for real-time analysis
import { useDebouncedCallback } from "use-debounce";

const analyzeDebounced = useDebouncedCallback(
  async (text: string) => {
    if (text.length > 50) {
      // Only analyze if enough text
      const result = await analyzeSentiment(text);
      setSentiment(result);
    }
  },
  1000 // Wait 1 second after typing stops
);
```

### 3. Bulk News Import & Analysis

```typescript
async function importAndAnalyzeBulk(newsArticles: any[]) {
  const results = [];

  for (const article of newsArticles) {
    try {
      const { article: created, sentiment } = await createAndAnalyzeNews({
        title: article.title,
        content: article.content,
        source: article.source,
        url: article.url,
      });

      results.push({ success: true, article: created, sentiment });
    } catch (error) {
      results.push({ success: false, error: error.message });
    }
  }

  return results;
}
```

## ⚡ Performance Tips

1. **Cache Results**: Sentiment analysis takes 2-5 seconds, cache in localStorage
2. **Batch When Possible**: Use `/analyze/batch` for multiple texts
3. **Debounce Real-time**: Don't analyze on every keystroke
4. **Pagination**: Always paginate news lists (don't load all at once)

## 🔧 Environment Setup

Add to `fe/.env.local`:

```bash
NEXT_PUBLIC_AI_API_URL=http://localhost:8000/api/v1
```

For Docker:

```bash
NEXT_PUBLIC_AI_API_URL=http://ai:8000/api/v1
```

## 🚨 Error Handling

```typescript
try {
  const result = await analyzeSentiment(text);
  // Success
} catch (error) {
  if (error.response?.status === 404) {
    // Not found
  } else if (error.response?.status === 400) {
    // Bad request (e.g., text too long)
  } else {
    // Network or server error
  }
}
```

## 📝 Notes

- **OpenAI Key Required**: Make sure AI service has valid `OPENAI_API_KEY` in `.env`
- **Rate Limits**: OpenAI API has rate limits, implement retry logic
- **Fallback Mode**: If OpenAI unavailable, service uses keyword-based analysis (lower accuracy)
- **Max Text Length**: 10,000 characters for quick analysis

## 📚 Full Documentation

Xem file `FE_INTEGRATION_GUIDE.md` để có hướng dẫn chi tiết với:

- Complete API reference
- Advanced examples
- UI component templates
- Authentication setup
- Error handling patterns

---

**Ready to use!** Copy `ai-api.ts` và bắt đầu integrate. 🚀
