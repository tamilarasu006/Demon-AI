"""MongoDB API routes — expose conversation persistence endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, Path
from pydantic import BaseModel

router = APIRouter(prefix="/api/mongo", tags=["mongodb"])


from OpenDEMON.server.models import StrictBaseModel
from pydantic import Field

class ConversationBody(StrictBaseModel):
    id: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_\-]+$")
    title: Optional[str] = Field(default="New chat", max_length=255)
    model: Optional[str] = Field(default="", max_length=100)
    messages: Optional[List[Dict[str, Any]]] = None


from OpenDEMON.server.limiter import limiter
from OpenDEMON.core.config import load_config

@router.get("/health")
@limiter.limit(lambda: load_config().server.ratelimit_public)
async def mongo_health(request: Request):
    """Check MongoDB connectivity."""
    try:
        from OpenDEMON.mongodb import ping
        ok = ping()
        return {"mongodb": "connected" if ok else "unavailable"}
    except Exception as exc:
        return {"mongodb": "error", "detail": str(exc)}


@router.get("/conversations")
def list_conversations():
    """List all stored conversations."""
    try:
        from OpenDEMON.mongodb import list_conversations as _list
        return {"conversations": _list(limit=200)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str = Path(..., max_length=100, pattern=r"^[a-zA-Z0-9_\-]+$")):
    """Get a specific conversation."""
    try:
        from OpenDEMON.mongodb import load_conversation
        doc = load_conversation(conversation_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return doc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/conversations")
def save_conversation(body: ConversationBody):
    """Save or update a conversation."""
    try:
        from OpenDEMON.mongodb import save_conversation as _save
        ok = _save(body.id, body.model_dump())
        return {"ok": ok, "id": body.id}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str = Path(..., max_length=100, pattern=r"^[a-zA-Z0-9_\-]+$")):
    """Delete a conversation."""
    try:
        from OpenDEMON.mongodb import delete_conversation as _delete
        ok = _delete(conversation_id)
        return {"ok": ok}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
