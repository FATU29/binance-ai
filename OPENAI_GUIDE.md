# OpenAI Integration Guide

## 🤖 Overview

The AI Service now integrates OpenAI's GPT models for advanced sentiment analysis of crypto and financial news. This provides more accurate, context-aware sentiment analysis compared to simple keyword matching.

## 🔑 Setup

### 1. Get OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-...`)

### 2. Configure Environment

Add your OpenAI API key to `.env` file:

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Important**: Never commit your API key to git! The `.gitignore` file already excludes `.env`.

### 3. Choose Your Model

The service supports various OpenAI models. Configure in your request or use defaults:

| Model           | Cost | Speed     | Quality   | Recommended For      |
| --------------- | ---- | --------- | --------- | -------------------- |
| `gpt-4o-mini`   | $    | Fast      | Good      | Production (default) |
| `gpt-4o`        | $$$  | Medium    | Excellent | High accuracy needs  |
| `gpt-4-turbo`   | $$   | Medium    | Excellent | Complex analysis     |
| `gpt-3.5-turbo` | $    | Very Fast | Good      | High volume          |

**Default**: `gpt-4o-mini` (best balance of cost and quality)

## 📊 Features

### 1. **Crypto-Specific Sentiment Analysis**

The AI is trained to understand:

- **Financial terminology**: bull/bear markets, support/resistance, etc.
- **Crypto slang**: moon, pump, dump, HODL, etc.
- **Market sentiment**: fear, greed, FOMO, FUD
- **News impact**: adoption, regulation, partnerships, hacks

### 2. **Sentiment Labels**

The AI returns one of these labels:

- `bullish` - Positive crypto market sentiment
- `bearish` - Negative crypto market sentiment
- `neutral` - Balanced or unclear sentiment
- `positive` - General positive sentiment
- `negative` - General negative sentiment

### 3. **Confidence Scores**

- **sentiment_score**: 0.0 (most bearish) to 1.0 (most bullish)
- **confidence**: 0.0 to 1.0 (AI's confidence in its analysis)

### 4. **Automatic Fallback**

If OpenAI API is unavailable or fails:

- Automatically falls back to keyword-based analysis
- Service continues without interruption
- Lower confidence scores indicate fallback mode

## 🚀 API Endpoints

### 1. Quick Text Analysis

**Endpoint**: `POST /api/v1/ai/analyze/quick`

Analyze any text instantly without database storage.

```bash
curl -X POST "http://localhost:8000/api/v1/ai/analyze/quick" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Bitcoin breaks through $100K resistance, bullish momentum continues!",
    "use_openai": true,
    "model_version": "gpt-4o-mini"
  }'
```

**Response**:

```json
{
  "sentiment_label": "bullish",
  "sentiment_score": 0.92,
  "confidence": 0.88,
  "model_version": "gpt-4o-mini-2024-07-18"
}
```

### 2. Analyze News Article

**Endpoint**: `POST /api/v1/ai/analyze/news/{article_id}`

Analyze a stored news article and save the result.

```bash
curl -X POST "http://localhost:8000/api/v1/ai/analyze/news/1"
```

**Response**:

```json
{
  "id": 1,
  "news_article_id": 1,
  "sentiment_label": "bullish",
  "sentiment_score": 0.85,
  "confidence": 0.9,
  "model_version": "gpt-4o-mini-2024-07-18",
  "created_at": "2024-12-20T08:55:00Z",
  "updated_at": "2024-12-20T08:55:00Z"
}
```

### 3. Batch Analysis

**Endpoint**: `POST /api/v1/ai/analyze/batch`

Analyze multiple texts in one request (max 10).

```bash
curl -X POST "http://localhost:8000/api/v1/ai/analyze/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Bitcoin surges to new highs",
      "Market crash imminent, experts warn",
      "Sideways trading continues"
    ],
    "model_version": "gpt-4o-mini"
  }'
```

### 4. Get Latest Analysis

**Endpoint**: `GET /api/v1/ai/news/{article_id}/latest`

Get the most recent sentiment analysis for an article.

```bash
curl "http://localhost:8000/api/v1/ai/news/1/latest"
```

## 💡 Usage Examples

### Python Example

```python
import httpx
import asyncio

async def analyze_crypto_news():
    async with httpx.AsyncClient() as client:
        # Quick analysis
        response = await client.post(
            "http://localhost:8000/api/v1/ai/analyze/quick",
            params={"text": "Ethereum 2.0 upgrade successful, staking rewards increase"},
            json={"use_openai": True}
        )
        result = response.json()
        print(f"Sentiment: {result['sentiment_label']} ({result['sentiment_score']:.2f})")
        print(f"Confidence: {result['confidence']:.2f}")

asyncio.run(analyze_crypto_news())
```

### JavaScript Example

```javascript
async function analyzeSentiment(text) {
  const response = await fetch(
    "http://localhost:8000/api/v1/ai/analyze/quick?text=" +
      encodeURIComponent(text),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ use_openai: true }),
    }
  );

  const result = await response.json();
  console.log(
    `Sentiment: ${result.sentiment_label} (${result.sentiment_score})`
  );
  return result;
}

analyzeSentiment("Bitcoin ETF approval drives massive rally");
```

### cURL Examples

```bash
# Analyze with OpenAI
curl -X POST "http://localhost:8000/api/v1/ai/analyze/quick?text=Bitcoin%20hits%20ATH&use_openai=true"

# Force keyword fallback
curl -X POST "http://localhost:8000/api/v1/ai/analyze/quick?text=Market%20crash&use_openai=false"

# Use specific model
curl -X POST "http://localhost:8000/api/v1/ai/analyze/quick?text=ETH%20bullish&use_openai=true&model_version=gpt-4o"
```

## 💰 Cost Management

### Pricing (as of Dec 2024)

| Model         | Input (per 1M tokens) | Output (per 1M tokens) |
| ------------- | --------------------- | ---------------------- |
| gpt-4o-mini   | $0.15                 | $0.60                  |
| gpt-4o        | $2.50                 | $10.00                 |
| gpt-3.5-turbo | $0.50                 | $1.50                  |

### Cost Estimates

Typical news article (~500 words = ~700 tokens):

| Model         | Cost per Analysis |
| ------------- | ----------------- |
| gpt-4o-mini   | ~$0.0002          |
| gpt-4o        | ~$0.003           |
| gpt-3.5-turbo | ~$0.0006          |

**Example**: 1,000 analyses/day with gpt-4o-mini = ~$0.20/day = ~$6/month

### Tips to Minimize Costs

1. **Use gpt-4o-mini** for most analyses (default)
2. **Batch requests** when analyzing multiple texts
3. **Cache results** - don't re-analyze the same article
4. **Set spending limits** in OpenAI dashboard
5. **Use fallback mode** for non-critical analyses

## 🔒 Security Best Practices

1. **Never expose API keys**

   - Use environment variables
   - Don't commit `.env` to git
   - Rotate keys regularly

2. **Rate Limiting**

   - OpenAI has built-in rate limits
   - Implement application-level limits if needed

3. **Error Handling**

   - Service gracefully falls back on API errors
   - Logs all errors for monitoring

4. **Access Control**
   - Add authentication to your endpoints
   - Use API keys for external access

## 📈 Monitoring

### Check OpenAI Usage

1. Visit [OpenAI Usage Dashboard](https://platform.openai.com/usage)
2. Monitor daily/monthly spending
3. Set up billing alerts

### Application Logs

The service logs all OpenAI calls:

```
2024-12-20 08:55:00 [info] Calling OpenAI API for sentiment analysis
2024-12-20 08:55:01 [info] OpenAI sentiment analysis completed sentiment=bullish score=0.85
```

## 🐛 Troubleshooting

### Issue: "OpenAI API key not found"

**Solution**:

1. Check `.env` file has `OPENAI_API_KEY=sk-...`
2. Restart the application
3. Verify the key is valid in OpenAI dashboard

### Issue: Rate limit errors

**Solution**:

- Wait a few seconds between requests
- Use batch endpoint for multiple texts
- Upgrade OpenAI plan if needed

### Issue: Service falls back to keywords

**Causes**:

- No API key configured
- API key invalid or expired
- OpenAI service temporarily down
- Network connectivity issues

**Check logs** for specific error messages.

## 🎯 Advanced Configuration

### Custom System Prompt

Edit `app/services/sentiment_service.py` to customize the AI's behavior:

```python
system_prompt = """Your custom instructions here..."""
```

### Temperature Settings

- **Lower (0.0-0.3)**: More consistent, deterministic
- **Higher (0.7-1.0)**: More creative, varied

Current: `0.3` (good for consistent sentiment analysis)

### Max Tokens

Current: `200` tokens for response (sufficient for sentiment analysis)

Increase if you need more detailed explanations.

## 📚 Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [OpenAI Pricing](https://openai.com/pricing)
- [Best Practices for Production](https://platform.openai.com/docs/guides/production-best-practices)
- [Rate Limits](https://platform.openai.com/docs/guides/rate-limits)

## ✅ Testing

Test the integration using the interactive docs:

1. Open http://localhost:8000/docs
2. Navigate to "AI Analytics (OpenAI)" section
3. Try the endpoints with sample text
4. Check responses and logs

---

**Note**: The service works without OpenAI (using keyword fallback), but OpenAI provides significantly more accurate and context-aware results for crypto/financial news.
