#!/bin/bash

# Comprehensive test script for AI Service API with OpenAI integration
# Tests all AI analytics endpoints with various scenarios

BASE_URL="http://localhost:8000"
API_V1="${BASE_URL}/api/v1"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo "🤖 AI Service API - Comprehensive Tests"
echo "=========================================="
echo ""

# Function to print test header
print_test() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}TEST $1: $2${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Function to check HTTP status
check_status() {
    if [ "$1" -eq 200 ] || [ "$1" -eq 201 ]; then
        echo -e "${GREEN}✅ Status: $1 (Success)${NC}"
        return 0
    else
        echo -e "${RED}❌ Status: $1 (Failed)${NC}"
        return 1
    fi
}

# Test 0: Check if server is running
print_test "0" "Health Check - Is server running?"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_V1}/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$HEALTH_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✅ Server is running${NC}"
    echo "Response:"
    echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"
else
    echo -e "${RED}❌ Server is not running (Status: $HTTP_CODE)${NC}"
    echo ""
    echo "Start the server with:"
    echo "  cd /home/fat/code/cryto-final-project/ai"
    echo "  .venv/bin/python main.py"
    echo ""
    exit 1
fi

# Test 1: Quick Analysis - Bullish sentiment
print_test "1" "Quick Analysis - Bullish Sentiment (with OpenAI)"
echo "Text: 'Bitcoin surges to new all-time high as institutional adoption accelerates'"
echo ""
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_V1}/ai/analyze/quick?text=Bitcoin%20surges%20to%20new%20all-time%20high%20as%20institutional%20adoption%20accelerates&use_openai=true")
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')
check_status "$HTTP_CODE"
echo "Response:"
echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"

# Test 2: Quick Analysis - Bearish sentiment
print_test "2" "Quick Analysis - Bearish Sentiment (with OpenAI)"
echo "Text: 'Market crash imminent as regulatory concerns mount, investors panic sell'"
echo ""
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_V1}/ai/analyze/quick?text=Market%20crash%20imminent%20as%20regulatory%20concerns%20mount%2C%20investors%20panic%20sell&use_openai=true")
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')
check_status "$HTTP_CODE"
echo "Response:"
echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"

# Test 3: Quick Analysis - Neutral sentiment
print_test "3" "Quick Analysis - Neutral Sentiment (with OpenAI)"
echo "Text: 'Bitcoin trading sideways, consolidating around current levels'"
echo ""
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_V1}/ai/analyze/quick?text=Bitcoin%20trading%20sideways%2C%20consolidating%20around%20current%20levels&use_openai=true")
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')
check_status "$HTTP_CODE"
echo "Response:"
echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"

# Test 4: Keyword Fallback Analysis
print_test "4" "Keyword Fallback Analysis (without OpenAI)"
echo "Text: 'Ethereum bullish momentum continues with major upgrade'"
echo ""
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_V1}/ai/analyze/quick?text=Ethereum%20bullish%20momentum%20continues%20with%20major%20upgrade&use_openai=false")
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')
check_status "$HTTP_CODE"
echo "Response:"
echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"

# Test 5: Batch Analysis
print_test "5" "Batch Analysis - Multiple Texts"
echo "Analyzing 3 different sentiments in batch..."
echo ""
BATCH_DATA='{
  "texts": [
    "Bitcoin breaks through resistance, HODL strong!",
    "Bear market continues, massive sell-off expected",
    "Stable price action, waiting for catalyst"
  ],
  "model_version": "gpt-4o-mini"
}'
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_V1}/ai/analyze/batch" \
  -H "Content-Type: application/json" \
  -d "$BATCH_DATA")
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')
check_status "$HTTP_CODE"
echo "Response:"
echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"

# Test 6: Create News Article
print_test "6" "Create News Article"
echo "Creating a test news article..."
echo ""
NEWS_DATA='{
  "title": "Bitcoin ETF Approval Drives Massive Rally",
  "content": "Bitcoin surged to new all-time highs following the approval of spot Bitcoin ETFs by the SEC. Institutional investors are flooding into the market with record inflows. Analysts predict continued bullish momentum as mainstream adoption accelerates.",
  "source": "CryptoNews Daily",
  "url": "https://example.com/btc-etf-rally-'$(date +%s)'",
  "category": "cryptocurrency",
  "author": "John Crypto"
}'
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_V1}/news" \
  -H "Content-Type: application/json" \
  -d "$NEWS_DATA")
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')
check_status "$HTTP_CODE"
echo "Response:"
echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"

# Extract article ID for next tests
ARTICLE_ID=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 0))" 2>/dev/null)

if [ "$ARTICLE_ID" != "0" ] && [ ! -z "$ARTICLE_ID" ]; then
    # Test 7: Analyze News Article
    print_test "7" "Analyze News Article by ID"
    echo "Analyzing article ID: $ARTICLE_ID"
    echo ""
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_V1}/ai/analyze/news/${ARTICLE_ID}")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
    RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')
    check_status "$HTTP_CODE"
    echo "Response:"
    echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"

    # Test 8: Get Latest Analysis
    print_test "8" "Get Latest Analysis for Article"
    echo "Fetching latest sentiment analysis for article ID: $ARTICLE_ID"
    echo ""
    RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${API_V1}/ai/news/${ARTICLE_ID}/latest")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
    RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')
    check_status "$HTTP_CODE"
    echo "Response:"
    echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"
else
    echo -e "${YELLOW}⚠️  Skipping Tests 7-8 (Article creation failed)${NC}"
fi

# Test 9: Crypto-Specific Terms
print_test "9" "Crypto Slang Recognition"
echo "Text: 'ETH to the moon! HODL strong, pump incoming, bullish AF'"
echo ""
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_V1}/ai/analyze/quick?text=ETH%20to%20the%20moon!%20HODL%20strong%2C%20pump%20incoming%2C%20bullish%20AF&use_openai=true")
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')
check_status "$HTTP_CODE"
echo "Response:"
echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"

# Test 10: Long Text Analysis
print_test "10" "Long Text Analysis"
echo "Testing with longer news article text..."
echo ""
LONG_TEXT="The%20cryptocurrency%20market%20experienced%20significant%20volatility%20today%20as%20Bitcoin%20prices%20fluctuated%20between%2095000%20and%20102000.%20Market%20analysts%20attribute%20this%20movement%20to%20increasing%20institutional%20adoption%20and%20positive%20regulatory%20developments.%20Major%20financial%20institutions%20continue%20to%20show%20interest%20in%20digital%20assets%2C%20with%20several%20announcing%20plans%20to%20offer%20cryptocurrency%20services%20to%20their%20clients."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_V1}/ai/analyze/quick?text=${LONG_TEXT}&use_openai=true")
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')
check_status "$HTTP_CODE"
echo "Response:"
echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"

# Test 11: Error Handling - Empty Text
print_test "11" "Error Handling - Empty Text"
echo "Testing with empty text (should fail)..."
echo ""
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_V1}/ai/analyze/quick?text=&use_openai=true")
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')
if [ "$HTTP_CODE" -eq 400 ] || [ "$HTTP_CODE" -eq 422 ]; then
    echo -e "${GREEN}✅ Correctly rejected empty text (Status: $HTTP_CODE)${NC}"
else
    echo -e "${RED}❌ Should have returned 400/422 (Got: $HTTP_CODE)${NC}"
fi
echo "Response:"
echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"

# Test 12: Mixed Sentiment
print_test "12" "Mixed Sentiment Analysis"
echo "Text: 'Bitcoin shows strength but regulatory concerns remain'"
echo ""
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_V1}/ai/analyze/quick?text=Bitcoin%20shows%20strength%20but%20regulatory%20concerns%20remain&use_openai=true")
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')
check_status "$HTTP_CODE"
echo "Response:"
echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Test Suite Completed!${NC}"
echo "=========================================="
echo ""
echo "� Summary:"
echo "  • Quick Analysis Tests: 5"
echo "  • Batch Analysis: 1"
echo "  • News Article Workflow: 3"
echo "  • Error Handling: 1"
echo "  • Total Tests: 12"
echo ""
echo "📚 Additional Resources:"
echo "  • Interactive Docs: ${BASE_URL}/docs"
echo "  • API Documentation: ${BASE_URL}/redoc"
echo "  • OpenAI Guide: ./OPENAI_GUIDE.md"
echo "  • Usage Examples: ./examples/openai_usage_example.py"
echo ""
echo "🔑 Note:"
echo "  • Tests use OpenAI if OPENAI_API_KEY is set in .env"
echo "  • Falls back to keyword analysis if no API key"
echo "  • Check logs for detailed analysis information"
echo ""
