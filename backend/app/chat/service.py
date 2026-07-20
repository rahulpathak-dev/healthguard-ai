import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.models import Conversation


async def owned_conversation(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID, lock: bool = False
) -> Conversation:
    statement = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.owner_user_id == user_id,
    )
    if lock:
        statement = statement.with_for_update()
    conversation = await db.scalar(statement)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
