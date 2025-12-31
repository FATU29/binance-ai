from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Crypto News AI Analyzer",
    description="AI-powered sentiment analysis and news analysis for cryptocurrency",
    version="1.0.0"
)

# Global variables for models (lazy loading)
sentiment_analyzer = None
ner_model = None

def load_models():
    """Load AI models on startup"""
    global sentiment_analyzer, ner_model
    
    try:
        logger.info("Loading AI models...")
        
        # Try to load FinBERT for sentiment analysis
        try:
            from transformers import pipeline
            sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                device=-1  # Use CPU (-1) or GPU (0)
            )
            logger.info("FinBERT sentiment analyzer loaded successfully!")
        except Exception as e:
            logger.warning(f"Failed to load FinBERT: {e}")
            logger.info("Using fallback sentiment analyzer...")
            from transformers import pipeline
            sentiment_analyzer = pipeline("sentiment-analysis")
        
        # Try to load NER model
        try:
            from transformers import pipeline
            ner_model = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                device=-1
            )
            logger.info("NER model loaded successfully!")
        except Exception as e:
            logger.warning(f"Failed to load NER model: {e}")
            ner_model = None
        
        logger.info("All models loaded successfully!")
        
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        logger.info("Service will start but AI features may be limited")

@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    load_models()

# Request/Response Models
class SentimentRequest(BaseModel):
    text: str
    
class SentimentResponse(BaseModel):
    label: str
    score: float
    confidence: float
    keywords: List[str]
    reasoning: str

class EntityRequest(BaseModel):
    text: str
    
class EntityResponse(BaseModel):
    entities: List[dict]
    trading_pairs: List[str]
    cryptocurrencies: List[str]

class PriceImpactRequest(BaseModel):
    text: str
    trading_pair: Optional[str] = None
    
class PriceImpactResponse(BaseModel):
    direction: str  # up, down, neutral
    magnitude: str  # high, medium, low
    timeframe: str  # short, medium, long
    confidence: float
    reasoning: str

# Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Crypto News AI Analyzer",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "sentiment_model_loaded": sentiment_analyzer is not None,
        "ner_model_loaded": ner_model is not None
    }

@app.post("/analyze/sentiment", response_model=SentimentResponse)
async def analyze_sentiment(request: SentimentRequest):
    """Analyze sentiment of news text"""
    if not sentiment_analyzer:
        raise HTTPException(status_code=503, detail="Sentiment model not loaded")
    
    try:
        # Truncate text to avoid memory issues (512 tokens max for BERT)
        text = request.text[:512]
        
        # Analyze sentiment
        result = sentiment_analyzer(text)
        
        # Extract keywords (simple version)
        keywords = extract_keywords(request.text)
        
        # Convert label to standardized format
        label = result[0]["label"].lower()
        score = result[0]["score"]
        
        # Map FinBERT labels to standard labels
        if label in ["positive", "bullish"]:
            label = "positive"
            final_score = score
        elif label in ["negative", "bearish"]:
            label = "negative"
            final_score = -score
        else:
            label = "neutral"
            final_score = 0.0
        
        reasoning = f"AI analysis using FinBERT model. Detected {label} sentiment with {score:.2%} confidence."
        
        return SentimentResponse(
            label=label,
            score=final_score,
            confidence=score,
            keywords=keywords[:10],  # Top 10 keywords
            reasoning=reasoning
        )
        
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/analyze/entities", response_model=EntityResponse)
async def extract_entities(request: EntityRequest):
    """Extract entities from news text"""
    if not ner_model:
        # Fallback to simple keyword extraction
        cryptos = extract_crypto_mentions(request.text)
        return EntityResponse(
            entities=[],
            trading_pairs=[f"{c}USDT" for c in cryptos],
            cryptocurrencies=cryptos
        )
    
    try:
        # Truncate text
        text = request.text[:512]
        
        # Extract entities
        entities = ner_model(text)
        
        # Extract cryptocurrencies from entities
        cryptos = extract_crypto_from_entities(entities)
        
        # Generate trading pairs
        trading_pairs = [f"{crypto}USDT" for crypto in cryptos]
        
        return EntityResponse(
            entities=entities,
            trading_pairs=trading_pairs,
            cryptocurrencies=cryptos
        )
        
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        # Fallback to simple extraction
        cryptos = extract_crypto_mentions(request.text)
        return EntityResponse(
            entities=[],
            trading_pairs=[f"{c}USDT" for c in cryptos],
            cryptocurrencies=cryptos
        )

@app.post("/analyze/price-impact", response_model=PriceImpactResponse)
async def analyze_price_impact(request: PriceImpactRequest):
    """Predict price impact from news"""
    if not sentiment_analyzer:
        raise HTTPException(status_code=503, detail="Sentiment model not loaded")
    
    try:
        # First get sentiment
        sentiment_result = sentiment_analyzer(request.text[:512])
        
        # Map sentiment to price impact
        label = sentiment_result[0]["label"].lower()
        confidence = sentiment_result[0]["score"]
        
        # Determine direction
        if label in ["positive", "bullish"]:
            direction = "up"
        elif label in ["negative", "bearish"]:
            direction = "down"
        else:
            direction = "neutral"
        
        # Determine magnitude based on confidence
        if confidence > 0.85:
            magnitude = "high"
        elif confidence > 0.65:
            magnitude = "medium"
        else:
            magnitude = "low"
        
        # Determine timeframe based on content
        text_lower = request.text.lower()
        if any(word in text_lower for word in ["regulation", "policy", "law", "government"]):
            timeframe = "long"
        elif any(word in text_lower for word in ["partnership", "adoption", "integration"]):
            timeframe = "medium"
        else:
            timeframe = "short"
        
        reasoning = f"Based on {label} sentiment (confidence: {confidence:.2%}), " \
                   f"predicting {direction} movement with {magnitude} magnitude in {timeframe} term."
        
        return PriceImpactResponse(
            direction=direction,
            magnitude=magnitude,
            timeframe=timeframe,
            confidence=confidence,
            reasoning=reasoning
        )
        
    except Exception as e:
        logger.error(f"Price impact analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Helper functions
def extract_keywords(text: str) -> List[str]:
    """Extract important keywords from text"""
    keywords = []
    
    # Important crypto-related keywords
    important_words = [
        "bitcoin", "ethereum", "btc", "eth", "crypto", "blockchain",
        "surge", "rally", "crash", "fall", "bullish", "bearish",
        "gain", "loss", "profit", "decline", "rise", "drop",
        "regulation", "adoption", "partnership", "hack", "scam"
    ]
    
    text_lower = text.lower()
    for word in important_words:
        if word in text_lower:
            keywords.append(word)
    
    return keywords

def extract_crypto_mentions(text: str) -> List[str]:
    """Extract cryptocurrency mentions from text"""
    cryptos = []
    text_upper = text.upper()
    
    crypto_list = [
        "BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOGE",
        "DOT", "MATIC", "AVAX", "LINK", "LTC", "XLM", "XMR", "TRX"
    ]
    
    crypto_names = {
        "BITCOIN": "BTC",
        "ETHEREUM": "ETH",
        "BINANCE COIN": "BNB",
        "RIPPLE": "XRP",
        "CARDANO": "ADA",
        "SOLANA": "SOL",
        "DOGECOIN": "DOGE",
        "POLKADOT": "DOT",
        "POLYGON": "MATIC",
        "AVALANCHE": "AVAX",
        "CHAINLINK": "LINK",
        "LITECOIN": "LTC",
    }
    
    # Check direct symbols
    for crypto in crypto_list:
        if crypto in text_upper:
            if crypto not in cryptos:
                cryptos.append(crypto)
    
    # Check crypto names
    for name, symbol in crypto_names.items():
        if name in text_upper:
            if symbol not in cryptos:
                cryptos.append(symbol)
    
    return cryptos

def extract_crypto_from_entities(entities: List[dict]) -> List[str]:
    """Extract cryptocurrencies from NER entities"""
    cryptos = []
    
    for entity in entities:
        word = entity.get("word", "").replace("##", "").upper()
        
        # Check if it's a known crypto
        if word in ["BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOGE"]:
            if word not in cryptos:
                cryptos.append(word)
    
    return cryptos

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
