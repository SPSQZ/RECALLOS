import os
import logging
from dotenv import load_dotenv
from openai import AuthenticationError, OpenAI

from fastapi import FastAPI,Depends,HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from sqlalchemy import text


import models  
from database import engine,sessionlocal,Base
load_dotenv()

logger = logging.getLogger(__name__)
api_key = os.getenv("NEBIUS_API_KEY")
client = OpenAI(
    api_key=api_key,
    base_url="https://api.studio.nebius.ai/v1/"
) if api_key else None
Base.metadata.create_all(bind = engine)

app = FastAPI(title = "RecallOS API")

# database session
def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()

# request schema
class conversationcreate(BaseModel):
    title: str = "new conversation"

# home endpoint
@app.get("/")
def home():
    return {
        "message": "Welcome to RecallOS",
        "status": "Backend is running"
    }
# health endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
# database check
@app.get("/db-check")
def database_check(db: Session = Depends(get_db)):
    db.execute(__import__("sqlalchemy").text("select 1"))
    return {
        "status": "connected",
        "database": "SQLite"
    }
# create a conversation
@app.post("/conversations")
def create_conversation(
    conversation: conversationcreate,
    db: Session = Depends(get_db)
):
    new_conversation = models.Conversation(
        title = conversation.title
    )
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)

    return{
        "id": new_conversation.id,
        "title": new_conversation.title,
        "created_at": new_conversation.created_at
    }

# get all conversation
@app.get("/conversations")
def get_conversation(db: Session = Depends(get_db)):
    conversations = (
        db.query(models.Conversation).order_by(models.Conversation.id.desc())
    ).all()
    return conversations

# get one conversation by id

@app.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id:int,
    db: Session = Depends(get_db)):
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()
    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="conversation not found"
        )
    return conversation

# Request schema for creating a message
class MessageCreate(BaseModel):
    role: str
    content: str


# Create a message inside a conversation
@app.post("/conversations/{conversation_id}/messages")
def create_message(
    conversation_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    if message.role not in ("user", "assistant"):
        raise HTTPException(
            status_code=400,
            detail="Role must be 'user' or 'assistant'"
        )

    if not message.content.strip():
        raise HTTPException(
            status_code=400,
            detail="Message content cannot be empty"
        )

    new_message = models.Message(
        conversation_id=conversation_id,
        role=message.role,
        content=message.content
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return {
        "id": new_message.id,
        "conversation_id": new_message.conversation_id,
        "role": new_message.role,
        "content": new_message.content,
        "created_at": new_message.created_at
    }


# Get all messages in a conversation
@app.get("/conversations/{conversation_id}/messages")
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

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
            "created_at": item.created_at
        }
        for item in messages
    ]

# chat with AI
@app.post("/conversations/{conversation_id}/chat")
def chat_with_ai(
    conversation_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    if not message.content.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )

    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )
    # Save the user's message
    user_message = models.Message(
        conversation_id=conversation_id,
        role="user",
        content=message.content
    )
    db.add(user_message)
    db.commit()
    # Load the conversation history
    history = (
        db.query(models.Message)
        .filter(
            models.Message.conversation_id == conversation_id
        )
        .order_by(models.Message.id)
        .all()
    )

    ai_messages = [
        {
            "role": item.role,
            "content": item.content
        }
        for item in history
        if item.role in ("user", "assistant")
    ]

    if client is None:
        answer = (
            f"Demo mode: You said '{message.content}'. "
            "RecallOS saved your message successfully."
            "connect an ai provider later for intelligent response"
        )
    else:
        try:
            completion = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are RecallOS, a helpful AI assistant. "
                            "Answer clearly and accurately."
                        )
                    },
                    *ai_messages
                ],
                max_tokens=500
            )

            answer = completion.choices[0].message.content

            if not answer:
                raise HTTPException(
                    status_code=502,
                    detail="The AI returned an empty response"
                )

        except HTTPException:
            raise
        except AuthenticationError as exc:
            db.rollback()
            raise HTTPException(
                status_code=502,
                detail=(
                    "Nebius rejected NEBIUS_API_KEY. Replace it with a valid "
                    "Nebius API key and restart the app."
                )
            ) from exc
        except Exception as exc:
            db.rollback()
            logger.exception("Nebius chat request failed")
            raise HTTPException(
                status_code=502,
                detail="AI request failed. Check the server logs."
            ) from exc

    # Save the assistant's reply
    assistant_message = models.Message(
        conversation_id=conversation_id,
        role="assistant",
        content=answer
    )

    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return {
        "conversation_id": conversation_id,
        "user_message": message.content,
        "assistant_message": answer,
        "assistant_message_id": assistant_message.id
    }