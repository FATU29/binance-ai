"""Chat endpoint for AI chatbox."""

import uuid
from datetime import datetime

import structlog
from fastapi import APIRouter, HTTPException, Header, status

from app.schemas.chat import (
    ChatMessageRequest,
    ChatResponse,
    ChatMessage,
)
from app.services.chat_service import chat_service

router = APIRouter()
logger = structlog.get_logger()

# In-memory conversation storage (for development)
# In production, this should be stored in Redis or a database
conversations: dict[str, list[ChatMessage]] = {}


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a chat message to AI assistant",
    description="VIP-only feature: Chat with AI assistant about crypto trading. Maintains conversation context.",
)
async def chat(
    request: ChatMessageRequest,
    x_user_id: str | None = Header(None, alias="X-User-Id"),
    x_user_account_type: str | None = Header(None, alias="X-User-AccountType"),
) -> ChatResponse:
    """
    Chat with AI assistant (VIP only).

    This endpoint should be called through the API Gateway which validates
    VIP status. As a fallback, we also check the account type header.

    Args:
        request: Chat message request
        x_user_id: User ID from gateway (injected by authentication filter)
        x_user_account_type: Account type from gateway (injected by authentication filter)

    Returns:
        ChatResponse: AI assistant's response with conversation context

    Raises:
        HTTPException: If user is not VIP or if there's an error
    """
    # Validate VIP status (fallback check, gateway should handle this)
    if x_user_account_type != "VIP":
        logger.warning(
            "Non-VIP user attempted to access chat",
            user_id=x_user_id,
            account_type=x_user_account_type,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature is only available for VIP users. Please upgrade your account.",
        )

    # Get or create conversation ID
    conversation_id = request.conversation_id or f"conv-{uuid.uuid4().hex[:16]}"

    # Get conversation history
    history = conversations.get(conversation_id, [])

    # Create user message
    user_message = ChatMessage(
        id=f"user-{uuid.uuid4().hex[:12]}",
        role="user",
        content=request.message,
        timestamp=datetime.utcnow(),
    )

    # Add user message to history
    history.append(user_message)

    # Get AI response
    try:
        assistant_message = await chat_service.chat(
            user_message=request.message,
            conversation_history=history[:-1],  # Don't include the message we just added
        )

        # Add assistant message to history
        history.append(assistant_message)

        # Store updated conversation
        conversations[conversation_id] = history

        # Limit conversation history to last 50 messages to prevent memory issues
        if len(conversations[conversation_id]) > 50:
            conversations[conversation_id] = conversations[conversation_id][-50:]

        logger.info(
            "Chat message processed",
            conversation_id=conversation_id,
            user_id=x_user_id,
            message_count=len(history),
        )

        return ChatResponse(
            conversation_id=conversation_id,
            message=assistant_message,
            total_messages=len(history),
        )

    except ValueError as e:
        logger.error("Chat service configuration error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI chat service is temporarily unavailable. Please contact support.",
        ) from e
    except Exception as e:
        logger.error("Unexpected error in chat endpoint", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your message. Please try again.",
        ) from e


@router.delete(
    "/chat/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear conversation history",
    description="Delete a conversation and its history (VIP only).",
)
async def clear_conversation(
    conversation_id: str,
    x_user_account_type: str | None = Header(None, alias="X-User-AccountType"),
) -> None:
    """
    Clear a conversation's history.

    Args:
        conversation_id: The conversation ID to clear
        x_user_account_type: Account type from gateway

    Raises:
        HTTPException: If user is not VIP
    """
    # Validate VIP status
    if x_user_account_type != "VIP":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature is only available for VIP users.",
        )

    if conversation_id in conversations:
        del conversations[conversation_id]
        logger.info("Conversation cleared", conversation_id=conversation_id)
