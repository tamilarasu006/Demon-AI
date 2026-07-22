"""MongoDB API routes — expose conversation persistence endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/mongo", tags=["mongodb"])


class ConversationBody(BaseModel):
    id: str
    title: Optional[str] = "New chat"
    model: Optional[str] = ""
    messages: Optional[List[Dict[str, Any]]] = []


@router.get("/health")
def mongo_health():
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
def get_conversation(conversation_id: str):
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
def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    try:
        from OpenDEMON.mongodb import delete_conversation as _delete
        ok = _delete(conversation_id)
        return {"ok": ok}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
