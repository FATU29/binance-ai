"""Chat service for AI chatbox using OpenAI."""

import json
import re
import uuid
from datetime import datetime
from typing import Any

import httpx
import structlog
from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.chat import ChatMessage
from app.schemas.price_prediction import PricePredictionRequest
from app.services.price_prediction_service import price_prediction_service

logger = structlog.get_logger()


class ChatService:
    """Service for handling AI chatbox conversations using OpenAI."""

    def __init__(self) -> None:
        """Initialize ChatService with OpenAI client."""
        self.client: AsyncOpenAI | None = None
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("ChatService initialized with OpenAI client")
        else:
            logger.warning("ChatService initialized without OpenAI API key")

    def _extract_crypto_symbol(self, message: str) -> str | None:
        """
        Extract cryptocurrency symbol from user message.
        
        Args:
            message: User's message
            
        Returns:
            Symbol in USDT format (e.g., BTCUSDT) or None
        """
        # Common crypto symbols
        crypto_patterns = {
            r'\bbitcoin\b|\bbtc\b': 'BTCUSDT',
            r'\bethereum\b|\beth\b': 'ETHUSDT',
            r'\bsolana\b|\bsol\b': 'SOLUSDT',
            r'\bbinance coin\b|\bbnb\b': 'BNBUSDT',
            r'\bcardano\b|\bada\b': 'ADAUSDT',
            r'\bdogecoin\b|\bdoge\b': 'DOGEUSDT',
            r'\bripple\b|\bxrp\b': 'XRPUSDT',
            r'\bpolkadot\b|\bdot\b': 'DOTUSDT',
            r'\bavalanche\b|\bavax\b': 'AVAXUSDT',
            r'\bpolygon\b|\bmatic\b': 'MATICUSDT',
        }
        
        message_lower = message.lower()
        for pattern, symbol in crypto_patterns.items():
            if re.search(pattern, message_lower, re.IGNORECASE):
                return symbol
        
        return None
    
    def _is_prediction_request(self, message: str) -> bool:
        """
        Check if user is asking for price prediction.
        
        Args:
            message: User's message
            
        Returns:
            True if message is asking for prediction
        """
        prediction_keywords = [
            'dự đoán', 'predict', 'forecast', 'dự báo',
            'xu hướng', 'trend', 'giá', 'price',
            'tăng', 'giảm', 'rise', 'fall', 'drop',
            'phân tích', 'analyze', 'analysis',
            'khả năng', 'potential', 'outlook'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in prediction_keywords)
    
    def _get_available_tools(self) -> list[dict[str, Any]]:
        """
        Define available tools for OpenAI function calling (MCP pattern).
        
        Returns:
            List of tool definitions
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_crypto_price_prediction",
                    "description": "Dự đoán xu hướng tăng/giảm giá cryptocurrency dựa trên phân tích tin tức mới nhất. Sử dụng tool này khi user hỏi về dự đoán giá, xu hướng, hoặc phân tích coin cụ thể.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Cryptocurrency trading pair symbol (e.g., BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, ADAUSDT, DOGEUSDT)",
                                "enum": [
                                    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
                                    "ADAUSDT", "DOGEUSDT", "XRPUSDT", "DOTUSDT",
                                    "AVAXUSDT", "MATICUSDT"
                                ]
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Số lượng tin tức để phân tích (mặc định: 10)",
                                "default": 10,
                                "minimum": 5,
                                "maximum": 20
                            }
                        },
                        "required": ["symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_articles_db",
                    "description": "Search the internal database of cryptocurrency news articles. Use this tool to find recent information, emerging patterns, and data for predictive analysis. Essential for answering questions about market trends, news, or when user asks for research.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {
                                "type": "string",
                                "description": "Search keyword or topic (e.g., 'Bitcoin', 'regulation', 'DeFi', 'Ethereum upgrade')"
                            },
                            "symbol": {
                                "type": "string",
                                "description": "Optional cryptocurrency symbol to filter results (e.g., 'BTC', 'ETH', 'SOL')"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of articles to retrieve (default: 10)",
                                "default": 10,
                                "minimum": 5,
                                "maximum": 30
                            }
                        },
                        "required": ["keyword"]
                    }
                }
            }
        ]
    
    async def _execute_tool(self, tool_name: str, tool_args: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a tool function call.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            
        Returns:
            Tool execution result
        """
        if tool_name == "get_crypto_price_prediction":
            try:
                symbol = tool_args.get("symbol", "BTCUSDT")
                limit = tool_args.get("limit", 10)
                
                logger.info(
                    "Executing price prediction tool",
                    symbol=symbol,
                    limit=limit
                )
                
                # Call prediction service
                request = PricePredictionRequest(symbol=symbol, limit=limit)
                prediction_result, news_articles = await price_prediction_service.predict_price(request)
                
                # Format result for AI
                return {
                    "success": True,
                    "symbol": symbol,
                    "prediction": prediction_result.prediction,
                    "confidence": prediction_result.confidence,
                    "sentiment_summary": prediction_result.sentiment_summary,
                    "reasoning": prediction_result.reasoning,
                    "key_factors": prediction_result.key_factors,
                    "news_analyzed": len(news_articles),
                    "analyzed_at": prediction_result.analyzed_at.isoformat()
                }
            except Exception as e:
                logger.error(
                    "Tool execution failed",
                    tool_name=tool_name,
                    error=str(e)
                )
                return {
                    "success": False,
                    "error": f"Failed to get prediction: {str(e)}"
                }
        
        elif tool_name == "search_articles_db":
            try:
                keyword = tool_args.get("keyword", "")
                symbol = tool_args.get("symbol", "")
                limit = tool_args.get("limit", 10)
                
                logger.info(
                    "Executing search_articles_db tool",
                    keyword=keyword,
                    symbol=symbol,
                    limit=limit
                )
                
                # Build search query
                search_query = keyword
                if symbol:
                    search_query = f"{symbol} {keyword}".strip()
                
                # Call crawler service API
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{settings.CRAWLER_SERVICE_URL}/api/news/search",
                        params={
                            "keyword": search_query,
                            "limit": limit
                        },
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        articles = data.get("data", {}).get("items", [])
                        
                        if not articles:
                            return {
                                "success": True,
                                "articles_found": 0,
                                "message": f"No articles found for keyword: {search_query}",
                                "articles": []
                            }
                        
                        # Format articles for AI
                        formatted_articles = []
                        for article in articles[:limit]:
                            formatted_articles.append({
                                "id": article.get("id"),
                                "title": article.get("title"),
                                "summary": article.get("summary", ""),
                                "source": article.get("source"),
                                "published_at": article.get("published_at"),
                                "url": article.get("url", "")
                            })
                        
                        logger.info(
                            "Articles retrieved successfully",
                            count=len(formatted_articles),
                            keyword=keyword
                        )
                        
                        return {
                            "success": True,
                            "articles_found": len(formatted_articles),
                            "search_query": search_query,
                            "articles": formatted_articles
                        }
                    else:
                        logger.error(
                            "Failed to fetch articles from crawler",
                            status_code=response.status_code
                        )
                        return {
                            "success": False,
                            "error": f"Failed to fetch articles: HTTP {response.status_code}"
                        }
                        
            except Exception as e:
                logger.error(
                    "Tool execution failed",
                    tool_name=tool_name,
                    error=str(e)
                )
                return {
                    "success": False,
                    "error": f"Failed to search articles: {str(e)}"
                }
        
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }

    async def chat(
        self,
        user_message: str,
        conversation_history: list[ChatMessage] | None = None,
    ) -> ChatMessage:
        """
        Send a chat message and get AI response with function calling (MCP pattern).
        AI can automatically call price prediction tool when needed.

        Args:
            user_message: User's message
            conversation_history: Previous messages in the conversation

        Returns:
            ChatMessage: AI assistant's response

        Raises:
            ValueError: If OpenAI API key is not configured
        """
        if not self.client or not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")
        
        # Build system prompt for Advanced Research Assistant with MCP
        system_prompt = (
            "### Role\n"
            "You are an Advanced Research Assistant integrated via Model Context Protocol (MCP). "
            "Your primary function is to provide predictive insights based on the internal database of articles "
            "and real-time cryptocurrency market predictions.\n\n"
            
            "### Core Instructions\n"
            "1. **Data Retrieval**: For research queries, use the `search_articles_db` tool to find the most recent and relevant information.\n"
            "2. **Price Predictions**: For price forecast queries, use the `get_crypto_price_prediction` tool.\n"
            "3. **Synthesis & Prediction**: Analyze retrieved data to identify emerging patterns and provide a 'Future Outlook'.\n"
            "4. **Source Attribution**: Always cite specific articles or publication dates from the database.\n"
            "5. **UI Integration (Crucial)**: At the very end of your response, you MUST provide 3 follow-up questions labeled as 'SUGGESTIONS'. Format them exactly like this:\n"
            "   [SUGGESTIONS]\n"
            "   - Question 1?\n"
            "   - Question 2?\n"
            "   - Question 3?\n\n"
            
            "### Tools Available\n"
            "- `search_articles_db`: Search internal database of cryptocurrency news articles\n"
            "- `get_crypto_price_prediction`: Get real-time price predictions with confidence scores\n\n"
            
            "### Tone & Style\n"
            "- Analytical, objective, and professional\n"
            "- If the database lacks recent information, explicitly state: 'Based on current database records, no recent data is available for a prediction.'\n\n"
            
            "### Output Template\n"
            "- **Executive Summary**: (Brief overview of findings)\n"
            "- **Predictive Insight**: (Forecast based on the data)\n"
            "- **Confidence Level**: [High/Medium/Low]\n"
            "- **Key Data Points**: (Cite specific articles with dates)\n"
            "- [SUGGESTIONS]\n\n"
            
            "### Response Formatting for Predictions\n"
            "When you receive prediction data, format your response with visual indicators:\n"
            "- For BULLISH predictions: Use 📈 🚀 💹 ⬆️ emojis\n"
            "- For BEARISH predictions: Use 📉 ⬇️ 🔻 emojis\n"
            "- For NEUTRAL predictions: Use ➡️ ⚖️ 😐 emojis\n\n"
            
            "Always include:\n"
            "1. **Prediction icon and direction** (e.g., 📈 TĂNG GIÁ or 📉 GIẢM GIÁ)\n"
            "2. **Confidence percentage** prominently displayed\n"
            "3. **Key reasoning** from the tool data\n"
            "4. **Disclaimer** about not being financial advice\n"
            "5. **[SUGGESTIONS]** section with 3 follow-up questions\n\n"
            
            "### Tools Available\n"
            "You have access to the `get_crypto_price_prediction` tool to fetch real-time predictions.\n"
            "Use this tool when users ask about price predictions, trends, or analysis for specific cryptocurrencies.\n"
            "Supported coins: Bitcoin (BTCUSDT), Ethereum (ETHUSDT), Solana (SOLUSDT), BNB (BNBUSDT), "
            "Cardano (ADAUSDT), Dogecoin (DOGEUSDT), Ripple (XRPUSDT), Polkadot (DOTUSDT), "
            "Avalanche (AVAXUSDT), Polygon (MATICUSDT).\n\n"
            
            "### Response Formatting\n"
            "When you receive prediction data from the tool, format your response with visual indicators:\n"
            "- For BULLISH predictions: Use 📈 🚀 💹 ⬆️ emojis at the start\n"
            "- For BEARISH predictions: Use 📉 ⬇️ 🔻 emojis at the start\n"
            "- For NEUTRAL predictions: Use ➡️ ⚖️ 😐 emojis at the start\n\n"
            "Always include:\n"
            "1. **Prediction icon and direction** (e.g., 📈 TĂNG GIÁ or 📉 GIẢM GIÁ)\n"
            "2. **Confidence percentage** prominently displayed\n"
            "3. **Key reasoning** from the tool data\n"
            "4. **Key factors** that influence the prediction\n"
            "5. **Disclaimer** about not being financial advice\n\n"
            
            "### Context & Analysis\n"
            "- Analyze recent market movements, news, and sentiment in cryptocurrency markets.\n"
            "- Prioritize information from the last 7-30 days for relevance.\n"
            "- If conflicting information exists, highlight the most recent and reliable sources.\n\n"
            
            "### Task Guidelines\n"
            "1. **Summarize**: Extract key facts from market data and recent developments.\n"
            "2. **Analyze**: Identify trends, sentiment (bullish/bearish/neutral), and market shifts.\n"
            "3. **Predict**: Based on patterns found, provide a 'Likely Outcome' or 'Future Projection'.\n"
            "4. **Confidence Score**: Assign a confidence level (0-100%) to predictions based on data quality.\n\n"
            
            "### Constraints\n"
            "- Always cite timeframes or recent events when making predictions.\n"
            "- If data is limited, state: 'Limited data available for a high-confidence prediction.'\n"
            "- Do not provide direct financial advice; maintain a professional, analytical tone.\n"
            "- Be concise but informative.\n"
            "- If you don't know something, admit it honestly rather than speculating.\n\n"
            
            "### Communication Style\n"
            "- Professional yet conversational\n"
            "- Use clear, accessible language while maintaining analytical depth\n"
            "- Support claims with reasoning\n"
            "- Be helpful in explaining complex concepts when asked"
        )
        
        # Build conversation context
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                messages.append({"role": msg.role, "content": msg.content})

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        try:
            logger.info(
                "Sending chat request to OpenAI with function calling",
                message_count=len(messages),
                user_message_length=len(user_message),
            )

            # Get available tools
            tools = self._get_available_tools()
            
            # Call OpenAI API with function calling enabled
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                tools=tools,
                tool_choice="auto",  # Let AI decide when to use tools
                temperature=0.7,
                max_tokens=800,  # Increased for detailed prediction responses
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )
            
            response_message = response.choices[0].message
            
            # Check if AI wants to call a function
            if response_message.tool_calls:
                logger.info(
                    "AI requested tool execution",
                    tool_count=len(response_message.tool_calls)
                )
                
                # Add AI's response to messages
                messages.append(response_message)
                
                # Execute all tool calls
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(
                        "Executing tool",
                        function=function_name,
                        args=function_args
                    )
                    
                    # Execute the tool
                    tool_result = await self._execute_tool(function_name, function_args)
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(tool_result)
                    })
                
                # Call OpenAI again with tool results
                logger.info("Calling OpenAI with tool results")
                second_response = await self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=800,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                )
                
                # Extract final assistant's response
                assistant_content = second_response.choices[0].message.content or "I'm sorry, I couldn't generate a response."
                
                logger.info(
                    "Chat response generated with tool execution",
                    response_length=len(assistant_content),
                    tokens_used=second_response.usage.total_tokens if second_response.usage else 0,
                )
            else:
                # No tool call, direct response
                assistant_content = response_message.content or "I'm sorry, I couldn't generate a response."
                
                logger.info(
                    "Chat response generated without tools",
                    response_length=len(assistant_content),
                    tokens_used=response.usage.total_tokens if response.usage else 0,
                )

            # Create response message
            assistant_message = ChatMessage(
                id=f"assistant-{uuid.uuid4().hex[:12]}",
                role="assistant",
                content=assistant_content,
                timestamp=datetime.utcnow(),
            )

            return assistant_message

        except Exception as e:
            logger.error("Error in chat service", error=str(e), exc_info=True)
            # Return a friendly error message to the user
            return ChatMessage(
                id=f"assistant-{uuid.uuid4().hex[:12]}",
                role="assistant",
                content="I'm sorry, I'm having trouble processing your request right now. Please try again later.",
                timestamp=datetime.utcnow(),
            )


# Singleton instance
chat_service = ChatService()
