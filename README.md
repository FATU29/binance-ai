# Crypto News AI Analyzer

AI-powered sentiment analysis and news analysis service for cryptocurrency news.

## Features

- **Sentiment Analysis**: Using FinBERT (financial BERT) for accurate crypto sentiment
- **Entity Extraction**: Identify cryptocurrencies and trading pairs from text
- **Price Impact Prediction**: Predict potential price movements based on news
- **RESTful API**: FastAPI-based API for easy integration

## Quick Start

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the service
python main.py
# Or with uvicorn:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build image
docker build -t crypto-ai-service .

# Run container
docker run -p 8000:8000 crypto-ai-service
```

### Docker Compose (with full stack)

```bash
cd ../crawl-news
docker-compose up -d
```

## API Endpoints

### Health Check

```bash
curl http://localhost:8000/health
```

### Sentiment Analysis

```bash
curl -X POST http://localhost:8000/analyze/sentiment \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Bitcoin price surges to new all-time high as institutional adoption grows"
  }'
```

Response:
```json
{
  "label": "positive",
  "score": 0.85,
  "confidence": 0.85,
  "keywords": ["bitcoin", "surge", "high", "adoption"],
  "reasoning": "AI analysis using FinBERT model..."
}
```

### Entity Extraction

```bash
curl -X POST http://localhost:8000/analyze/entities \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Bitcoin and Ethereum show strong performance"
  }'
```

Response:
```json
{
  "entities": [...],
  "trading_pairs": ["BTCUSDT", "ETHUSDT"],
  "cryptocurrencies": ["BTC", "ETH"]
}
```

### Price Impact Prediction

```bash
curl -X POST http://localhost:8000/analyze/price-impact \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Major exchange announces Bitcoin ETF approval",
    "trading_pair": "BTCUSDT"
  }'
```

Response:
```json
{
  "direction": "up",
  "magnitude": "high",
  "timeframe": "medium",
  "confidence": 0.92,
  "reasoning": "Based on positive sentiment..."
}
```

## Models

### FinBERT
- **Model**: `ProsusAI/finbert`
- **Purpose**: Financial sentiment analysis
- **Accuracy**: ~94% on financial data
- **Labels**: positive, negative, neutral

### BERT NER
- **Model**: `dslim/bert-base-NER`
- **Purpose**: Named entity recognition
- **Entities**: Organizations, locations, persons

## Performance

- **Sentiment Analysis**: ~500ms per request
- **Entity Extraction**: ~300ms per request
- **Price Impact**: ~600ms per request

## Environment Variables

```bash
# Optional: For GPU acceleration
CUDA_VISIBLE_DEVICES=0

# Optional: For model caching
TRANSFORMERS_CACHE=/path/to/cache
```

## Development

### Adding New Models

1. Install model dependencies
2. Add loading logic in `load_models()`
3. Create endpoint in `main.py`
4. Add tests

### Testing

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## Integration with Golang Backend

The backend calls this service via HTTP:

```go
// In ai_service.go
resp, err := http.Post(
    "http://localhost:8000/analyze/sentiment",
    "application/json",
    bytes.NewBuffer(jsonData),
)
```

## Troubleshooting

### Models Not Loading
- Check internet connection (models download on first run)
- Increase timeout if needed
- Check disk space (~500MB per model)

### Out of Memory
- Reduce batch size
- Use CPU instead of GPU for smaller deployments
- Truncate input text to 512 tokens

### Slow Performance
- Use GPU if available (set `device=0` in pipeline)
- Cache model in memory
- Use lighter models for production

## License

MIT

