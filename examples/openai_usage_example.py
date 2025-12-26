"""
Example usage of AI Service API with OpenAI sentiment analysis.

This script demonstrates how to use the API endpoints for analyzing
crypto news sentiment.
"""

import asyncio

import httpx


BASE_URL = "http://localhost:8000/api/v1"


async def quick_analysis_example():
    """Example: Quick sentiment analysis without database storage."""
    print("\n=== Quick Analysis Example ===\n")

    texts = [
        "Bitcoin breaks through $100K resistance, institutional buying intensifies!",
        "Market crash imminent as regulatory concerns mount",
        "Ethereum trading sideways, waiting for catalyst",
    ]

    async with httpx.AsyncClient() as client:
        for text in texts:
            print(f"Analyzing: {text[:50]}...")

            response = await client.post(
                f"{BASE_URL}/ai/analyze/quick",
                params={"text": text, "use_openai": True},
            )

            result = response.json()
            print(f"  Sentiment: {result['sentiment_label']}")
            print(f"  Score: {result['sentiment_score']:.2f}")
            print(f"  Confidence: {result['confidence']:.2f}")
            print(f"  Model: {result['model_version']}\n")


async def batch_analysis_example():
    """Example: Batch analysis of multiple texts."""
    print("\n=== Batch Analysis Example ===\n")

    texts = [
        "Bitcoin ATH reached!",
        "Bear market continues",
        "Stable price action today",
    ]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/ai/analyze/batch",
            json={"texts": texts, "model_version": "gpt-4o-mini"},
        )

        results = response.json()
        for i, result in enumerate(results, 1):
            print(f"{i}. \"{texts[i-1]}\"")
            print(f"   → {result['sentiment_label']} ({result['sentiment_score']:.2f})\n")


async def news_article_workflow():
    """Example: Complete workflow with news article."""
    print("\n=== News Article Workflow Example ===\n")

    async with httpx.AsyncClient() as client:
        # 1. Create a news article
        print("1. Creating news article...")
        article_data = {
            "title": "Bitcoin ETF Approval Drives Major Rally",
            "content": """
            Bitcoin surged to new all-time highs following the approval of spot Bitcoin ETFs.
            Institutional investors are flooding into the market, with record inflows reported.
            Analysts predict continued bullish momentum as adoption accelerates.
            """,
            "source": "CryptoNews",
            "url": "https://example.com/btc-etf-rally",
            "category": "cryptocurrency",
        }

        article_response = await client.post(
            f"{BASE_URL}/news",
            json=article_data,
        )

        if article_response.status_code == 201:
            article = article_response.json()
            article_id = article["id"]
            print(f"   Article created with ID: {article_id}\n")

            # 2. Analyze the article
            print("2. Analyzing article sentiment...")
            analysis_response = await client.post(
                f"{BASE_URL}/ai/analyze/news/{article_id}"
            )

            if analysis_response.status_code == 201:
                analysis = analysis_response.json()
                print(f"   Sentiment: {analysis['sentiment_label']}")
                print(f"   Score: {analysis['sentiment_score']:.2f}")
                print(f"   Confidence: {analysis['confidence']:.2f}\n")

                # 3. Retrieve the analysis
                print("3. Retrieving latest analysis...")
                latest_response = await client.get(
                    f"{BASE_URL}/ai/news/{article_id}/latest"
                )

                if latest_response.status_code == 200:
                    latest = latest_response.json()
                    print(f"   Found analysis ID: {latest['id']}")
                    print(f"   Created at: {latest['created_at']}\n")
        else:
            print(f"   Error: {article_response.status_code}")
            print(f"   {article_response.text}")


async def fallback_comparison():
    """Example: Compare OpenAI vs keyword fallback."""
    print("\n=== OpenAI vs Keyword Fallback Comparison ===\n")

    text = "Bitcoin price surges 20% on institutional adoption news"

    async with httpx.AsyncClient() as client:
        # With OpenAI
        print("Using OpenAI:")
        openai_response = await client.post(
            f"{BASE_URL}/ai/analyze/quick",
            params={"text": text, "use_openai": True},
        )
        openai_result = openai_response.json()
        print(f"  Sentiment: {openai_result['sentiment_label']}")
        print(f"  Score: {openai_result['sentiment_score']:.2f}")
        print(f"  Confidence: {openai_result['confidence']:.2f}\n")

        # With keyword fallback
        print("Using Keyword Fallback:")
        keyword_response = await client.post(
            f"{BASE_URL}/ai/analyze/quick",
            params={"text": text, "use_openai": False},
        )
        keyword_result = keyword_response.json()
        print(f"  Sentiment: {keyword_result['sentiment_label']}")
        print(f"  Score: {keyword_result['sentiment_score']:.2f}")
        print(f"  Confidence: {keyword_result['confidence']:.2f}\n")


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("AI Service API - OpenAI Sentiment Analysis Examples")
    print("=" * 60)

    try:
        # Run examples
        await quick_analysis_example()
        await batch_analysis_example()
        await fallback_comparison()
        # await news_article_workflow()  # Uncomment if you want to create articles

        print("\n" + "=" * 60)
        print("Examples completed successfully!")
        print("=" * 60 + "\n")

    except httpx.ConnectError:
        print("\n❌ Error: Cannot connect to API server")
        print("Make sure the server is running: python main.py")
        print("Server should be at: http://localhost:8000\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
