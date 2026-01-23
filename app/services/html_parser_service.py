"""AI-based HTML content parser using OpenAI."""

import json
import re
from html import unescape
from typing import Any

import structlog
from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.html_parser import HTMLParseRequest, HTMLParseResponse, ParsedArticle

logger = structlog.get_logger()


class HTMLParserService:
    """Service for parsing HTML content using AI to extract structured article data."""

    def __init__(self) -> None:
        """Initialize HTML parser service with OpenAI client."""
        self.model_version = settings.OPENAI_MODEL
        # Increased tokens to 2000 to handle full article content (can be up to 2000+ words)
        self.max_tokens = min(settings.OPENAI_MAX_TOKENS * 10, 2000)
        self.temperature = settings.OPENAI_TEMPERATURE
        self.client: AsyncOpenAI | None = None

        # Initialize OpenAI client if API key is available
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info(
                "HTML Parser service initialized with OpenAI",
                model=self.model_version,
                max_tokens=self.max_tokens,
            )
        else:
            logger.warning("OpenAI API key not found. HTML parser will use fallback method.")

    async def parse_html(self, request: HTMLParseRequest) -> HTMLParseResponse:
        """
        Parse HTML content to extract structured article data using AI.

        This method uses OpenAI to intelligently extract:
        - Title
        - Main content (cleaned text)
        - Summary
        - Author
        - Published date
        - Image URL
        - Tags/Categories
        - Language

        Args:
            request: HTMLParseRequest containing HTML content and optional context

        Returns:
            HTMLParseResponse with parsed article data and confidence score
        """
        # Clean HTML content (remove scripts, styles, etc.)
        cleaned_html = self._clean_html(request.html_content)

        # Use AI if available, otherwise fall back to basic extraction
        if self.client and settings.OPENAI_API_KEY:
            return await self._parse_with_ai(cleaned_html, request)
        else:
            logger.info("Using fallback HTML parsing method")
            return await self._parse_with_fallback(cleaned_html, request)

    async def _parse_with_ai(
        self, cleaned_html: str, request: HTMLParseRequest
    ) -> HTMLParseResponse:
        """Parse HTML using OpenAI GPT models."""
        try:
            # Increased HTML preview to 12000 chars to ensure full content extraction
            # Prioritize main content area but keep meta tags for context
            html_preview = self._extract_relevant_html(cleaned_html, 12000)
            if len(cleaned_html) > 12000:
                html_preview += "\n\n[... HTML content truncated - focus on main article content above ...]"

            system_prompt = """You are an expert web content extractor specializing in news articles. Extract COMPLETE structured article data from HTML.

CRITICAL REQUIREMENTS:
- title: Main article title (required, must extract accurately)
- content: COMPLETE FULL article text body (REQUIRED - extract ALL paragraphs, ALL sentences, ALL content)
  * DO NOT truncate or summarize the content
  * Extract EVERY paragraph from the article body
  * Include all text content, preserve paragraph structure
  * Minimum 500+ characters expected for full articles
  * Remove only navigation, ads, comments, footer - keep ALL article text

OPTIONAL FIELDS (extract if available):
- summary: Brief summary/excerpt (first paragraph or meta description)
- author: Author name
- published_at: Publication date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
- image_url: Main article image URL (PRIORITY: og:image > article:image > featured image > first large image)
- tags: List of tags/categories
- language: Language code (en, th, zh, etc.)

EXTRACTION RULES:
1. CONTENT IS CRITICAL: Extract the COMPLETE article body text - every paragraph, every sentence
2. For content: Look for <article>, <main>, or content containers - extract ALL text inside
3. Clean content: Remove HTML tags but preserve paragraph breaks (use \\n\\n between paragraphs)
4. Normalize whitespace: Multiple spaces to single space, but keep line breaks for paragraphs
5. For image_url: Check meta og:image first, then article/featured images, then first large image
6. Use null (not empty string) if optional field not found
7. Be adaptive: Handle different HTML structures, focus on semantic content extraction
8. If content seems incomplete, try to find more content in the HTML

Return ONLY valid JSON:
{
  "title": "string (full title)",
  "content": "string (COMPLETE full article text - all paragraphs, minimum 500+ chars)",
  "summary": "string or null",
  "author": "string or null",
  "published_at": "string or null",
  "image_url": "string or null",
  "tags": ["string"],
  "language": "string or null"
}"""

            user_prompt = f"""Extract COMPLETE article data from HTML. CRITICAL: Extract FULL article content (all paragraphs, all text).

URL: {request.url or 'Unknown'}
Source: {request.source_name or 'Unknown'}

HTML Content:
{html_preview}

IMPORTANT: 
- Extract the COMPLETE article content - every paragraph, every sentence
- Content should be 500+ characters for full articles
- Focus on <article>, <main>, or main content containers
- Extract title, FULL content, image_url (prioritize og:image), and all metadata."""

            logger.info(
                "Calling OpenAI for HTML parsing",
                model=self.model_version,
                html_length=len(cleaned_html),
                url=request.url,
            )

            response = await self.client.chat.completions.create(
                model=self.model_version,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")

            result_data = json.loads(content)

            # Validate and extract fields
            title = result_data.get("title", "").strip()
            article_content = result_data.get("content", "").strip()
            summary = result_data.get("summary", "").strip() or None
            author = result_data.get("author", "").strip() or None
            published_at = result_data.get("published_at", "").strip() or None
            image_url = result_data.get("image_url", "").strip() or None
            tags = result_data.get("tags", [])
            if not isinstance(tags, list):
                tags = []
            language = result_data.get("language", "").strip() or None

            # Validate required fields
            if not title or not article_content:
                logger.warning("AI parsing failed: missing required fields", title=bool(title), content=bool(article_content))
                return await self._parse_with_fallback(cleaned_html, request)
            
            # Validate content length - warn if too short (might be incomplete)
            if len(article_content) < 200:
                logger.warning("AI parsed content is very short (%d chars), might be incomplete", len(article_content))
            elif len(article_content) < 500:
                logger.info("AI parsed content is short (%d chars), might be a brief article", len(article_content))

            # Calculate confidence based on content quality
            confidence = self._calculate_confidence(title, article_content, result_data)

            article = ParsedArticle(
                title=title,
                content=article_content,
                summary=summary,
                author=author,
                published_at=published_at,
                image_url=image_url,
                tags=tags,
                language=language,
            )

            metadata = {
                "model": response.model,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "html_length": len(cleaned_html),
                "content_length": len(article_content),
            }

            logger.info(
                "AI HTML parsing completed",
                title_length=len(title),
                content_length=len(article_content),
                confidence=confidence,
            )

            return HTMLParseResponse(
                success=True,
                article=article,
                confidence=confidence,
                method="ai",
                metadata=metadata,
            )

        except json.JSONDecodeError as e:
            logger.error("Failed to parse OpenAI response as JSON", error=str(e))
            return await self._parse_with_fallback(cleaned_html, request)

        except Exception as e:
            logger.error(
                "AI HTML parsing failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return await self._parse_with_fallback(cleaned_html, request)

    async def _parse_with_fallback(
        self, cleaned_html: str, request: HTMLParseRequest
    ) -> HTMLParseResponse:
        """Fallback HTML parsing using basic regex and heuristics."""
        try:
            # Extract title (try multiple patterns)
            title = self._extract_title_fallback(cleaned_html)
            
            # Extract content (try to find main article text)
            content = self._extract_content_fallback(cleaned_html)
            
            # Extract other fields with basic patterns
            author = self._extract_author_fallback(cleaned_html)
            image_url = self._extract_image_fallback(cleaned_html)
            published_at = self._extract_date_fallback(cleaned_html)
            
            # Basic summary (first 200 chars of content)
            summary = content[:200] + "..." if len(content) > 200 else content

            if not title or not content:
                return HTMLParseResponse(
                    success=False,
                    article=None,
                    confidence=0.0,
                    method="fallback",
                    error="Could not extract required fields (title and content)",
                )

            confidence = 0.3  # Low confidence for fallback method

            article = ParsedArticle(
                title=title,
                content=content,
                summary=summary if len(content) > 200 else None,
                author=author,
                published_at=published_at,
                image_url=image_url,
                tags=[],
                language=None,
            )

            return HTMLParseResponse(
                success=True,
                article=article,
                confidence=confidence,
                method="fallback",
                metadata={"html_length": len(cleaned_html)},
            )

        except Exception as e:
            logger.error("Fallback HTML parsing failed", error=str(e))
            return HTMLParseResponse(
                success=False,
                article=None,
                confidence=0.0,
                method="fallback",
                error=f"Fallback parsing failed: {str(e)}",
            )

    def _clean_html(self, html: str) -> str:
        """Remove scripts, styles, and other non-content elements."""
        # Remove script tags
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        # Remove style tags
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
        # Remove comments
        html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
        # Remove noscript tags
        html = re.sub(r"<noscript[^>]*>.*?</noscript>", "", html, flags=re.DOTALL | re.IGNORECASE)
        return html

    def _extract_relevant_html(self, html: str, max_length: int) -> str:
        """Extract relevant HTML parts: head (meta tags) and main content area.
        Prioritizes main content to ensure full article extraction."""
        # Extract head section (for meta tags, especially og:image) - limit to 2000 chars
        head_match = re.search(r"<head[^>]*>(.*?)</head>", html, re.IGNORECASE | re.DOTALL)
        head_content = head_match.group(1)[:2000] if head_match else ""
        
        # Extract main content areas - prioritize article/main tags
        content_areas = []
        content_priorities = [
            (r"<article[^>]*>(.*?)</article>", "article"),
            (r"<main[^>]*>(.*?)</main>", "main"),
            (r'<div[^>]*class=["\'][^"\']*article[^"\']*["\'][^>]*>(.*?)</div>', "article-div"),
            (r'<div[^>]*class=["\'][^"\']*content[^"\']*["\'][^>]*>(.*?)</div>', "content-div"),
            (r"<body[^>]*>(.*?)</body>", "body"),
        ]
        
        for pattern, name in content_priorities:
            matches = re.finditer(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                content = match.group(1)
                # Filter out very short matches (likely not main content)
                if len(content.strip()) > 200:
                    content_areas.append((content, name))
                    # Take first 2 matches of each type
                    if len([c for c in content_areas if c[1] == name]) >= 2:
                        break
        
        # Sort by priority and length (longer content first)
        content_areas.sort(key=lambda x: (x[1] in ["article", "main"], len(x[0])), reverse=True)
        
        # Combine: head (limited) + main content (prioritized)
        head_part = head_content[:1500]  # Limit head to 1500 chars
        content_part = "\n".join([c[0] for c in content_areas[:3]])  # Take top 3 content areas
        
        # Calculate available space for content
        head_len = len(head_part)
        available_for_content = max_length - head_len - 200  # Reserve 200 for separators
        
        # Truncate content if needed, but try to keep complete paragraphs
        if len(content_part) > available_for_content:
            # Try to truncate at paragraph boundary
            truncated = content_part[:available_for_content]
            # Find last </p> or </div> to keep structure
            last_p = truncated.rfind("</p>")
            last_div = truncated.rfind("</div>")
            last_break = max(last_p, last_div)
            if last_break > available_for_content * 0.8:  # If break is reasonably close
                content_part = truncated[:last_break + 5]  # Include closing tag
            else:
                content_part = truncated
        
        relevant = head_part + "\n\n<!-- MAIN CONTENT -->\n" + content_part
        
        return relevant

    def _extract_title_fallback(self, html: str) -> str:
        """Extract title using fallback methods."""
        # Try meta tags first
        og_title = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if og_title:
            return unescape(og_title.group(1)).strip()
        
        # Try title tag
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = re.sub(r"<[^>]+>", "", title_match.group(1))
            title = unescape(title).strip()
            # Remove common suffixes
            title = re.sub(r"\s*[-|]\s*.*$", "", title)
            if len(title) > 10:
                return title
        
        # Try h1 tag
        h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
        if h1_match:
            title = re.sub(r"<[^>]+>", "", h1_match.group(1))
            title = unescape(title).strip()
            if len(title) > 10 and len(title) < 200:
                return title
        
        return ""

    def _extract_content_fallback(self, html: str) -> str:
        """Extract main content using fallback methods."""
        # Try article tag
        article_match = re.search(r"<article[^>]*>(.*?)</article>", html, re.IGNORECASE | re.DOTALL)
        if article_match:
            content = article_match.group(1)
            # Extract text from paragraphs
            paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", content, re.IGNORECASE | re.DOTALL)
            if paragraphs:
                text_content = "\n\n".join([
                    unescape(re.sub(r"<[^>]+>", "", p)).strip()
                    for p in paragraphs
                    if len(re.sub(r"<[^>]+>", "", p).strip()) > 50
                ])
                if len(text_content) > 200:
                    return text_content
        
        # Try main tag
        main_match = re.search(r"<main[^>]*>(.*?)</main>", html, re.IGNORECASE | re.DOTALL)
        if main_match:
            content = main_match.group(1)
            paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", content, re.IGNORECASE | re.DOTALL)
            if paragraphs:
                text_content = "\n\n".join([
                    unescape(re.sub(r"<[^>]+>", "", p)).strip()
                    for p in paragraphs
                    if len(re.sub(r"<[^>]+>", "", p).strip()) > 50
                ])
                if len(text_content) > 200:
                    return text_content
        
        return ""

    def _extract_author_fallback(self, html: str) -> str | None:
        """Extract author using fallback methods."""
        # Try meta tags
        author_meta = re.search(r'<meta\s+name=["\']author["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if author_meta:
            return unescape(author_meta.group(1)).strip()
        
        # Try common class patterns
        author_patterns = [
            r'<[^>]+class=["\'][^"\']*author[^"\']*["\'][^>]*>(.*?)</[^>]+>',
            r'<span[^>]*itemprop=["\']author["\'][^>]*>(.*?)</span>',
        ]
        for pattern in author_patterns:
            match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            if match:
                author = re.sub(r"<[^>]+>", "", match.group(1)).strip()
                if author and len(author) < 100:
                    return unescape(author)
        
        return None

    def _extract_image_fallback(self, html: str) -> str | None:
        """Extract main image URL using fallback methods with priority order."""
        # Priority 1: Open Graph image (most reliable)
        og_image = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if og_image:
            img_url = og_image.group(1).strip()
            if img_url and not img_url.startswith('data:'):  # Skip data URIs
                return img_url
        
        # Priority 2: Twitter card image
        twitter_image = re.search(r'<meta\s+name=["\']twitter:image["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if twitter_image:
            img_url = twitter_image.group(1).strip()
            if img_url and not img_url.startswith('data:'):
                return img_url
        
        # Priority 3: Article image meta tag
        article_image = re.search(r'<meta\s+property=["\']article:image["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if article_image:
            img_url = article_image.group(1).strip()
            if img_url and not img_url.startswith('data:'):
                return img_url
        
        # Priority 4: Images in article/main content with keywords
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        images = re.findall(img_pattern, html, re.IGNORECASE)
        
        # Look for images with relevant keywords in URL or attributes
        for img_url in images:
            img_url_lower = img_url.lower()
            if any(keyword in img_url_lower for keyword in ['article', 'post', 'featured', 'hero', 'main', 'cover', 'thumbnail']):
                if not img_url.startswith('data:') and len(img_url) > 10:
                    return img_url.strip()
        
        # Priority 5: First large image (not icon/logo)
        for img_url in images:
            if not img_url.startswith('data:'):
                # Skip small images (likely icons/logos)
                if not any(skip in img_url.lower() for skip in ['icon', 'logo', 'avatar', 'favicon']):
                    if len(img_url) > 20:  # Reasonable URL length
                        return img_url.strip()
        
        return None

    def _extract_date_fallback(self, html: str) -> str | None:
        """Extract published date using fallback methods."""
        # Try meta tags
        date_patterns = [
            r'<meta\s+property=["\']article:published_time["\']\s+content=["\']([^"\']+)["\']',
            r'<meta\s+name=["\']publish-date["\']\s+content=["\']([^"\']+)["\']',
            r'<time[^>]+datetime=["\']([^"\']+)["\']',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None

    def _calculate_confidence(self, title: str, content: str, result_data: dict[str, Any]) -> float:
        """Calculate confidence score based on extracted data quality."""
        confidence = 0.5  # Base confidence
        
        # Title quality
        if len(title) > 10 and len(title) < 200:
            confidence += 0.1
        
        # Content quality
        if len(content) > 500:
            confidence += 0.2
        elif len(content) > 200:
            confidence += 0.1
        
        # Additional fields increase confidence
        if result_data.get("author"):
            confidence += 0.05
        if result_data.get("published_at"):
            confidence += 0.05
        if result_data.get("image_url"):
            confidence += 0.05
        if result_data.get("tags") and len(result_data.get("tags", [])) > 0:
            confidence += 0.05
        
        return min(confidence, 1.0)


# Singleton instance
html_parser_service = HTMLParserService()
