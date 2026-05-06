"""Chat endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db.session import get_conn
from app.models.chat import ChatMessage, ChatRequest, ChatResponse
from app.services.llm.orchestrator import chat_turn, load_history
from app.services.profile import DatasetNotFoundError, build_profile

router = APIRouter(prefix="/api/datasets", tags=["chat"])


@router.post("/{dataset_id}/chat", response_model=ChatResponse)
def post_chat(dataset_id: str, request: ChatRequest) -> ChatResponse:
    try:
        with get_conn() as conn:
            # Touch the catalog to confirm dataset exists.
            build_profile(conn, dataset_id)
            return chat_turn(
                conn,
                dataset_id,
                user_message=request.message,
                conversation_id=request.conversation_id,
            )
    except DatasetNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found") from e


@router.get("/{dataset_id}/chat/history", response_model=list[ChatMessage])
def get_chat_history(dataset_id: str) -> list[ChatMessage]:
    try:
        with get_conn() as conn:
            build_profile(conn, dataset_id)
            return load_history(conn, dataset_id)
    except DatasetNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found") from e
