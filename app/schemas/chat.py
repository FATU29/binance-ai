"""Chat schemas for request/response validation."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    """Request schema for sending a chat message."""

    message: str = Field(..., min_length=1, max_length=2000, description="User's message")
    conversation_id: str | None = Field(
        None, description="Conversation ID for continuing a chat session"
    )


class ChatMessage(BaseModel):
    """Individual chat message in a conversation."""

    id: str = Field(..., description="Unique message ID")
    role: Literal["user", "assistant"] = Field(..., description="Message sender role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")


class ChatResponse(BaseModel):
    """Response schema for chat messages."""

    conversation_id: str = Field(..., description="Unique conversation ID")
    message: ChatMessage = Field(..., description="Assistant's response message")
    total_messages: int = Field(..., description="Total messages in this conversation")


class ConversationHistory(BaseModel):
    """Complete conversation history."""

    conversation_id: str = Field(..., description="Unique conversation ID")
    messages: list[ChatMessage] = Field(default_factory=list, description="All messages in conversation")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Conversation start time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last message time")
