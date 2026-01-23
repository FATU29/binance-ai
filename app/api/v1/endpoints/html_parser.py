"""AI-based HTML content parser endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.schemas.html_parser import HTMLParseRequest, HTMLParseResponse
from app.services.html_parser_service import html_parser_service

router = APIRouter()


@router.post("/parse-html", response_model=HTMLParseResponse)
async def parse_html(request: HTMLParseRequest) -> HTMLParseResponse:
    """
    Parse HTML content to extract structured article data using AI.

    This endpoint uses OpenAI to intelligently extract article information
    from HTML content, including:
    - Title
    - Main content
    - Summary
    - Author
    - Published date
    - Image URL
    - Tags/Categories
    - Language

    This is particularly useful when:
    - Website structure changes frequently
    - CSS selectors/XPath break
    - Dealing with JavaScript-rendered content
    - Parsing unknown website structures

    Args:
        request: HTMLParseRequest containing HTML content and optional context

    Returns:
        HTMLParseResponse with parsed article data and confidence score
    """
    if not request.html_content or len(request.html_content) < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HTML content is required and must be at least 100 characters",
        )

    try:
        result = await html_parser_service.parse_html(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse HTML: {str(e)}",
        )
