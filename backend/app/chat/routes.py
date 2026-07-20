import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.auth.rate_limit import enforce_rate_limit
from app.chat.models import ChatMessage, MessageFeedback
from app.chat.orchestration import recent_history, stream_assistant
from app.chat.schemas import (
    ChatBootstrap,
    ChatProfileOption,
    ConversationCreate,
    ConversationRename,
    ConversationView,
    FeedbackCreate,
    MessageCreate,
    MessageView,
    SuggestedQuestion,
)
from app.chat.service import owned_conversation
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.responses import ApiResponse
from app.dashboard.models import Conversation
from app.dashboard.service import profile_options
from app.db.session import get_db_session
from app.profiles.service import get_accessible_profile

router = APIRouter()
logger = get_logger()


@router.get("/bootstrap", response_model=ApiResponse[ChatBootstrap])
async def bootstrap(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)
) -> ApiResponse[ChatBootstrap]:
    available = await profile_options(db, user.id)
    return ApiResponse(
        data=ChatBootstrap(
            profiles=[
                ChatProfileOption(
                    id=profile.id, display_name=profile.display_name, kind=profile.kind.value
                )
                for profile, _, can_edit in available
                if can_edit
            ],
            suggested_questions=[
                SuggestedQuestion(
                    id="reports", text="How can I prepare questions about a lab report?"
                ),
                SuggestedQuestion(
                    id="medicines", text="What should I include in an accurate medicine list?"
                ),
                SuggestedQuestion(
                    id="symptoms", text="How should I organize symptom details for an appointment?"
                ),
            ],
            disclaimer=get_settings().medical_disclaimer,
            supported_languages=["en"],
        )
    )


@router.get("/conversations", response_model=ApiResponse[list[ConversationView]])
async def conversations(
    before: datetime | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[list[ConversationView]]:
    statement = select(Conversation).where(Conversation.owner_user_id == user.id)
    if before:
        statement = statement.where(Conversation.last_message_at < before)
    rows = (
        await db.scalars(statement.order_by(Conversation.last_message_at.desc()).limit(limit))
    ).all()
    return ApiResponse(data=[ConversationView.model_validate(item) for item in rows])


@router.post("/conversations", response_model=ApiResponse[ConversationView], status_code=201)
async def create_conversation(
    payload: ConversationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ConversationView]:
    await get_accessible_profile(db, payload.profile_id, user.id, require_edit=True)
    now = datetime.now(UTC)
    conversation = Conversation(
        profile_id=payload.profile_id,
        owner_user_id=user.id,
        title=payload.title,
        language=payload.language,
        created_at=now,
        last_message_at=now,
    )
    db.add(conversation)
    await db.flush()
    logger.info(
        "chat_conversation_created", user_id=str(user.id), conversation_id=str(conversation.id)
    )
    return ApiResponse(data=ConversationView.model_validate(conversation))


@router.patch("/conversations/{conversation_id}", response_model=ApiResponse[ConversationView])
async def rename_conversation(
    conversation_id: uuid.UUID,
    payload: ConversationRename,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ConversationView]:
    conversation = await owned_conversation(db, conversation_id, user.id)
    conversation.title = payload.title
    await db.flush()
    return ApiResponse(data=ConversationView.model_validate(conversation))


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    conversation = await owned_conversation(db, conversation_id, user.id)
    await db.delete(conversation)
    logger.info(
        "chat_conversation_deleted", user_id=str(user.id), conversation_id=str(conversation.id)
    )


@router.get(
    "/conversations/{conversation_id}/messages", response_model=ApiResponse[list[MessageView]]
)
async def messages(
    conversation_id: uuid.UUID,
    before_sequence: int | None = Query(default=None, ge=1),
    limit: int = Query(default=40, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[list[MessageView]]:
    await owned_conversation(db, conversation_id, user.id)
    statement = select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
    if before_sequence:
        statement = statement.where(ChatMessage.sequence < before_sequence)
    rows = (
        await db.scalars(
            statement.options(selectinload(ChatMessage.citations))
            .order_by(ChatMessage.sequence.desc())
            .limit(limit)
        )
    ).all()
    return ApiResponse(data=[MessageView.model_validate(item) for item in reversed(rows)])


@router.post("/conversations/{conversation_id}/messages")
async def create_message(
    conversation_id: uuid.UUID,
    payload: MessageCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    await enforce_rate_limit("chat-user", str(user.id), 30, 60)
    await enforce_rate_limit(
        "chat-ip", request.client.host if request.client else "unknown", 60, 60
    )
    conversation = await owned_conversation(db, conversation_id, user.id, lock=True)
    history = await recent_history(conversation.id)
    sequence = await db.scalar(
        select(func.coalesce(func.max(ChatMessage.sequence), 0)).where(
            ChatMessage.conversation_id == conversation.id
        )
    )
    now = datetime.now(UTC)
    language = payload.language or conversation.language
    user_message = ChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=payload.content,
        language=language,
        status="complete",
        sequence=int(sequence or 0) + 1,
        estimated_tokens=max(1, len(payload.content) // 4),
        created_at=now,
    )
    db.add(user_message)
    await db.flush()
    assistant = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content="",
        language=language,
        status="pending",
        sequence=int(sequence or 0) + 2,
        parent_message_id=user_message.id,
        estimated_tokens=0,
        created_at=now,
    )
    db.add(assistant)
    conversation.last_message_at = now
    await db.commit()
    logger.info(
        "chat_generation_started",
        user_id=str(user.id),
        conversation_id=str(conversation.id),
        assistant_id=str(assistant.id),
        input_characters=len(payload.content),
    )
    return StreamingResponse(
        stream_assistant(
            assistant.id, payload.content, language, history, user.id, conversation.id
        ),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@router.post("/messages/{message_id}/regenerate")
async def regenerate(
    message_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    assistant = await db.scalar(
        select(ChatMessage)
        .join(Conversation, Conversation.id == ChatMessage.conversation_id)
        .where(
            ChatMessage.id == message_id,
            ChatMessage.role == "assistant",
            Conversation.owner_user_id == user.id,
        )
    )
    if assistant is None or assistant.parent_message_id is None:
        raise HTTPException(status_code=404, detail="Message not found")
    original = await db.get(ChatMessage, assistant.parent_message_id)
    conversation = await owned_conversation(db, assistant.conversation_id, user.id, lock=True)
    if original is None or original.role != "user":
        raise HTTPException(status_code=409, detail="This response cannot be regenerated")
    await enforce_rate_limit("chat-regenerate", str(user.id), 10, 60)
    sequence = await db.scalar(
        select(func.coalesce(func.max(ChatMessage.sequence), 0)).where(
            ChatMessage.conversation_id == conversation.id
        )
    )
    replacement = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content="",
        language=assistant.language,
        status="pending",
        sequence=int(sequence or 0) + 1,
        parent_message_id=original.id,
        estimated_tokens=0,
        created_at=datetime.now(UTC),
    )
    db.add(replacement)
    conversation.last_message_at = replacement.created_at
    await db.commit()
    history = await recent_history(conversation.id)
    return StreamingResponse(
        stream_assistant(
            replacement.id,
            original.content,
            replacement.language,
            history,
            user.id,
            conversation.id,
        ),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@router.put("/messages/{message_id}/feedback", status_code=204)
async def feedback(
    message_id: uuid.UUID,
    payload: FeedbackCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    message = await db.scalar(
        select(ChatMessage)
        .join(Conversation, Conversation.id == ChatMessage.conversation_id)
        .where(
            ChatMessage.id == message_id,
            ChatMessage.role == "assistant",
            Conversation.owner_user_id == user.id,
        )
    )
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    existing = await db.scalar(
        select(MessageFeedback).where(
            MessageFeedback.message_id == message.id, MessageFeedback.user_id == user.id
        )
    )
    if existing:
        existing.rating = payload.rating
        existing.reason = payload.reason
    else:
        db.add(
            MessageFeedback(
                message_id=message.id,
                user_id=user.id,
                rating=payload.rating,
                reason=payload.reason,
                created_at=datetime.now(UTC),
            )
        )
