import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Ensure backend root is in python path
backend_root = Path(__file__).resolve().parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.core.config import settings
from app.core.nebius_client import nebius_client
from app.services.model_router import model_router
import models
from database import engine, sessionlocal, Base

load_dotenv()
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RecallOS API",
    description="Privacy-First Personal AI with Dynamic Nebius Model Routing",
    version="1.0.0",
)

# Enable CORS for frontend integration (Member 4)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database dependency
def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic Schemas
class ConversationCreate(BaseModel):
    title: str = "New Conversation"


class MessageCreate(BaseModel):
    role: str
    content: str


class PromptClassifyRequest(BaseModel):
    prompt: str = Field(..., description="Prompt text to evaluate for complexity")


class AgentGenerateRequest(BaseModel):
    prompt: str
    context: Optional[str] = None
    system_prompt: Optional[str] = (
        "You are RecallOS, a privacy-first personal AI with persistent memory."
    )
    max_tokens: int = 512
    temperature: float = 0.7


# =====================================================================
# Health & Status Endpoints
# =====================================================================


@app.get("/")
def home():
    return {
        "message": "Welcome to RecallOS",
        "status": "Backend is running",
        "nebius_mode": "live" if nebius_client.is_live else "simulation",
        "fast_model": settings.MODEL_FAST,
        "complex_model": settings.MODEL_COMPLEX,
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "nebius_live": nebius_client.is_live,
        "database": "SQLite",
    }


@app.get("/db-check")
def database_check(db: Session = Depends(get_db)):
    db.execute(__import__("sqlalchemy").text("SELECT 1"))
    return {"status": "connected", "database": "SQLite"}


# =====================================================================
# Member 1: Smart Model Router Endpoints
# =====================================================================


@app.get("/api/router/status")
def get_router_status():
    """Returns the live routing configuration, active models, and Nebius connectivity."""
    conn_info = nebius_client.verify_connection()
    return {
        "status": "active",
        "base_url": settings.NEBIUS_BASE_URL,
        "fast_model": settings.MODEL_FAST,
        "complex_model": settings.MODEL_COMPLEX,
        "complexity_threshold": settings.ROUTER_COMPLEXITY_THRESHOLD,
        "is_live_key": settings.is_key_valid,
        "connection": conn_info,
    }


@app.post("/api/router/classify")
def classify_prompt_endpoint(request: PromptClassifyRequest):
    """
    Evaluates prompt complexity and returns the intended route without triggering an LLM call.
    Ideal for real-time frontend indicators and Member 4's privacy audit panel.
    """
    evaluation = model_router.evaluate_complexity(request.prompt)
    return {
        "prompt": request.prompt,
        "route": evaluation["route"],
        "target_model": evaluation["target_model"],
        "complexity_score": evaluation["complexity_score"],
        "category": evaluation["category"],
        "signals": evaluation["signals"],
        "word_count": evaluation["word_count"],
    }


@app.post("/api/router/generate")
def agent_generate_endpoint(request: AgentGenerateRequest):
    """
    Direct model generation endpoint for Member 2's Agent & Tools loop.
    Routes dynamically to Nemotron Nano vs. Nemotron 3 Ultra and returns latency & routing metadata.
    """
    messages = []
    if request.context:
        messages.append(
            {
                "role": "system",
                "content": f"Context: {request.context}",
            }
        )
    messages.append({"role": "user", "content": request.prompt})

    result = model_router.route_and_generate(
        messages=messages,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        system_prompt=request.system_prompt,
    )

    return {
        "content": result["content"],
        "routing_metadata": result["routing_metadata"],
    }


# =====================================================================
# Conversations & Chat Endpoints (Updated with Smart Routing)
# =====================================================================


@app.post("/conversations")
def create_conversation(
    conversation: ConversationCreate, db: Session = Depends(get_db)
):
    new_conversation = models.Conversation(title=conversation.title)
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    return {
        "id": new_conversation.id,
        "title": new_conversation.title,
        "created_at": new_conversation.created_at,
    }


@app.get("/conversations")
def get_conversations(db: Session = Depends(get_db)):
    conversations = (
        db.query(models.Conversation)
        .order_by(models.Conversation.id.desc())
        .all()
    )
    return conversations


@app.get("/conversations/{conversation_id}")
def get_conversation_by_id(
    conversation_id: int, db: Session = Depends(get_db)
):
    conversation = (
        db.query(models.Conversation)
        .filter(models.Conversation.id == conversation_id)
        .first()
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.post("/conversations/{conversation_id}/messages")
def create_message(
    conversation_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(models.Conversation)
        .filter(models.Conversation.id == conversation_id)
        .first()
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if message.role not in ("user", "assistant"):
        raise HTTPException(
            status_code=400, detail="Role must be 'user' or 'assistant'"
        )

    if not message.content.strip():
        raise HTTPException(
            status_code=400, detail="Message content cannot be empty"
        )

    new_message = models.Message(
        conversation_id=conversation_id,
        role=message.role,
        content=message.content,
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return {
        "id": new_message.id,
        "conversation_id": new_message.conversation_id,
        "role": new_message.role,
        "content": new_message.content,
        "created_at": new_message.created_at,
    }


@app.get("/conversations/{conversation_id}/messages")
def get_messages(conversation_id: int, db: Session = Depends(get_db)):
    conversation = (
        db.query(models.Conversation)
        .filter(models.Conversation.id == conversation_id)
        .first()
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation_id)
        .order_by(models.Message.id)
        .all()
    )

    return [
        {
            "id": item.id,
            "conversation_id": item.conversation_id,
            "role": item.role,
            "content": item.content,
            "created_at": item.created_at,
        }
        for item in messages
    ]


@app.post("/conversations/{conversation_id}/chat")
def chat_with_ai(
    conversation_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db),
):
    """
    Main Chat Flow:
    1. Persists user prompt in SQLite.
    2. Gathers conversation context history.
    3. Smart Router dynamically assesses complexity & chooses Nemotron Nano vs. 3 Ultra.
    4. Measures accurate round-trip latency.
    5. Persists assistant reply.
    6. Returns assistant content PLUS rich routing metadata (model, latency, route, complexity).
    """
    if not message.content.strip():
        raise HTTPException(
            status_code=400, detail="Message cannot be empty"
        )

    conversation = (
        db.query(models.Conversation)
        .filter(models.Conversation.id == conversation_id)
        .first()
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 1. Save user's message
    user_message = models.Message(
        conversation_id=conversation_id,
        role="user",
        content=message.content,
    )
    db.add(user_message)
    db.commit()

    # 2. Gather conversation history
    history = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation_id)
        .order_by(models.Message.id)
        .all()
    )

    ai_messages = [
        {"role": item.role, "content": item.content}
        for item in history
        if item.role in ("user", "assistant")
    ]

    # 3. Route through Smart Model Router
    try:
        router_result = model_router.route_and_generate(
            messages=ai_messages,
            max_tokens=600,
        )
        answer = router_result["content"]
        routing_metadata = router_result["routing_metadata"]

    except Exception as exc:
        db.rollback()
        logger.exception("Model router inference failed")
        raise HTTPException(
            status_code=502,
            detail=f"Inference error through Nebius: {str(exc)}",
        ) from exc

    # 4. Save assistant reply
    assistant_message = models.Message(
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return {
        "conversation_id": conversation_id,
        "user_message": message.content,
        "assistant_message": answer,
        "assistant_message_id": assistant_message.id,
        "routing_metadata": routing_metadata,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
