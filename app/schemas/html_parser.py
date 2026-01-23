"""Pydantic schemas for AI-based HTML content parsing."""

from typing import Optional

from pydantic import BaseModel, Field


class HTMLParseRequest(BaseModel):
    """Request schema for HTML content parsing."""

    html_content: str = Field(..., description="Raw HTML content to parse", min_length=100)
    url: Optional[str] = Field(None, description="Source URL for context")
    source_name: Optional[str] = Field(None, description="Source website name for context")


class ParsedArticle(BaseModel):
    """Parsed article content structure."""

    title: str = Field(..., description="Article title")
    content: str = Field(..., description="Full article content (main text)")
    summary: Optional[str] = Field(None, description="Article summary or excerpt")
    author: Optional[str] = Field(None, description="Article author name")
    published_at: Optional[str] = Field(None, description="Publication date (ISO format or readable)")
    image_url: Optional[str] = Field(None, description="Main article image URL")
    tags: list[str] = Field(default_factory=list, description="Article tags or categories")
    language: Optional[str] = Field(None, description="Article language code (e.g., 'en', 'th')")


class HTMLParseResponse(BaseModel):
    """Response schema for HTML content parsing."""

    success: bool = Field(..., description="Whether parsing was successful")
    article: Optional[ParsedArticle] = Field(None, description="Parsed article data")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)")
    method: str = Field(..., description="Parsing method used ('ai' or 'fallback')")
    error: Optional[str] = Field(None, description="Error message if parsing failed")
    metadata: Optional[dict] = Field(None, description="Additional metadata about the parsing process")
