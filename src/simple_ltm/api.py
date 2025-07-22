"""
api.py
======

FastAPI application for the long-term memory system.
Provides REST API endpoints for managing user memories.
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic

from .memory import LongTermMemory
from .agent import MemoryAgent

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

app = FastAPI(
    title="Long-Term Memory API",
    description="API for managing user-specific long-term memories using ReAct agents",
    version="2.0.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global settings
DB_PATH = os.getenv("LTM_DB_PATH", "memory.db")
ANTHROPIC_MODEL = os.getenv("LTM_ANTHROPIC_MODEL", "claude-sonnet-4")

# ---------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    user_id: str = Field(..., description="Unique user identifier")
    message: str = Field(..., description="User's message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "alice123",
                "message": "My favorite color is blue"
            }
        }

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    reply: str = Field(..., description="Assistant's response")
    memory_updated: bool = Field(..., description="Whether memory was updated")
    
    class Config:
        json_schema_extra = {
            "example": {
                "reply": "I'll remember that your favorite color is blue!",
                "memory_updated": True
            }
        }

class MemoryResponse(BaseModel):
    """Response model for memory retrieval"""
    user_id: str = Field(..., description="User identifier")
    memory: str = Field(..., description="Current memory content")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "alice123",
                "memory": "Favorite color: blue. Likes hiking."
            }
        }

class MemoryUpdateRequest(BaseModel):
    """Request model for direct memory updates"""
    user_id: str = Field(..., description="User identifier")
    memory: str = Field(..., description="New memory content")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "alice123",
                "memory": "Favorite color: blue. Likes hiking. Has a cat named Mittens."
            }
        }

class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error details")

# ---------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------

def get_llm() -> ChatAnthropic:
    """Get configured LLM instance"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY environment variable not set"
        )
    return ChatAnthropic(model=ANTHROPIC_MODEL, temperature=0, api_key=api_key)

def get_memory_store() -> LongTermMemory:
    """Get memory store instance"""
    return LongTermMemory(DB_PATH)

# ---------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Long-Term Memory API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat",
            "get_memory": "/memory/{user_id}",
            "update_memory": "/memory",
            "health": "/health"
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    llm: ChatAnthropic = Depends(get_llm)
) -> ChatResponse:
    """
    Process a chat message and optionally update user's memory.
    
    The agent will decide if the message contains information worth remembering
    and automatically update the memory if needed.
    """
    try:
        # Create agent for this user
        agent = MemoryAgent(
            user_id=request.user_id,
            llm=llm,
            db_path=DB_PATH
        )
        
        # Process the message
        reply = await agent.chat(request.message)
        
        # Note: With ReAct pattern, we don't track memory updates explicitly
        # The agent handles it autonomously
        return ChatResponse(
            reply=reply,
            memory_updated=False  # This field is kept for API compatibility
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/{user_id}", response_model=MemoryResponse)
async def get_memory(
    user_id: str,
    memory_store: LongTermMemory = Depends(get_memory_store)
) -> MemoryResponse:
    """
    Retrieve the current memory for a specific user.
    
    Returns an empty string if the user has no stored memory.
    """
    try:
        memory = memory_store.read(user_id)
        return MemoryResponse(user_id=user_id, memory=memory)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/memory", response_model=MemoryResponse)
async def update_memory(
    request: MemoryUpdateRequest,
    memory_store: LongTermMemory = Depends(get_memory_store)
) -> MemoryResponse:
    """
    Directly update a user's memory.
    
    This bypasses the agent and directly sets the memory content.
    Use with caution as it replaces the entire memory.
    """
    try:
        memory_store.write(request.user_id, request.memory)
        return MemoryResponse(user_id=request.user_id, memory=request.memory)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memory/{user_id}")
async def clear_memory(
    user_id: str,
    memory_store: LongTermMemory = Depends(get_memory_store)
) -> Dict[str, str]:
    """
    Clear a user's memory by setting it to an empty string.
    """
    try:
        memory_store.write(user_id, "")
        return {"message": f"Memory cleared for user {user_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "agent": "react"}

# ---------------------------------------------------------------------
# Run the app
# ---------------------------------------------------------------------

def main():
    """Run the API server."""
    import uvicorn
    
    # Check for required environment variables
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Warning: ANTHROPIC_API_KEY environment variable not set!")
    
    # Run the server
    uvicorn.run(
        "simple_ltm.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main()