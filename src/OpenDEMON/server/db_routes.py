from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from OpenDEMON.server.models import StrictBaseModel
from pydantic import Field
from OpenDEMON.database.session import get_db_session
from OpenDEMON.database.repositories.conversations import ConversationRepository
from OpenDEMON.server.limiter import limiter
from OpenDEMON.core.config import load_config

router = APIRouter(prefix="/api/pg", tags=["postgres"])

class ConversationBody(StrictBaseModel):
    id: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_\-]+$")
    title: Optional[str] = Field(default="New chat", max_length=255)
    model: Optional[str] = Field(default="", max_length=100)
    messages: Optional[List[Dict[str, Any]]] = None

@router.get("/health")
@limiter.limit(lambda: load_config().server.ratelimit_public)
async def pg_health(request: Request, db: AsyncSession = Depends(get_db_session)):
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        return {"postgres": "connected"}
    except Exception as exc:
        return {"postgres": "error", "detail": str(exc)}

@router.get("/conversations")
async def list_conversations(request: Request, db: AsyncSession = Depends(get_db_session)):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    repo = ConversationRepository(db)
    convs = await repo.list_conversations(user_id)
    return {"conversations": [{"id": c.id, "title": c.title, "updated_at": c.updated_at} for c in convs]}

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    request: Request,
    conversation_id: str = Path(..., max_length=100, pattern=r"^[a-zA-Z0-9_\-]+$"),
    db: AsyncSession = Depends(get_db_session)
):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    repo = ConversationRepository(db)
    conv = await repo.get_conversation(user_id, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    messages = await repo.get_messages(user_id, conversation_id)
    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at,
        "messages": [{"role": m.role, "content": m.content, "created_at": m.created_at} for m in messages]
    }

@router.post("/conversations")
async def save_conversation(request: Request, body: ConversationBody, db: AsyncSession = Depends(get_db_session)):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    repo = ConversationRepository(db)
    conv = await repo.get_conversation(user_id, body.id)
    if not conv:
        conv = await repo.create_conversation(user_id, body.title)
    
    if body.messages:
        for msg in body.messages:
            # Basic save; assumes format
            await repo.add_message(user_id, body.id, msg.get("role", "user"), msg.get("content", ""))
            
    return {"ok": True, "id": conv.id}
