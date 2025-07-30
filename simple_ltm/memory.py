"""
memory.py
=========

Core long-term memory system using SQLite for persistence.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool

from .prompts import format_update_prompt


class LongTermMemory:
    """
    Simple SQLite-based long-term memory system.
    
    Stores one memory string per user in a relational database.
    """

    def __init__(self, db_path: str | Path = "memory.db"):
        """
        Initialize the memory system.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create the memory table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS memory(
                    user_id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );"""
            )
            conn.commit()

    def read(self, user_id: str) -> str:
        """
        Read a user's memory.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            The user's memory string, or empty string if none exists
        """
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "SELECT content FROM memory WHERE user_id = ?;", 
                (user_id,)
            ).fetchone()
            return result[0] if result else ""

    def write(self, user_id: str, content: str) -> None:
        """
        Write or update a user's memory.
        
        Args:
            user_id: The user's unique identifier
            content: The memory content to store
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO memory(user_id, content, updated_at) 
                   VALUES (?, ?, CURRENT_TIMESTAMP);""",
                (user_id, content)
            )
            conn.commit()

    def delete(self, user_id: str) -> None:
        """
        Delete a user's memory.
        
        Args:
            user_id: The user's unique identifier
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM memory WHERE user_id = ?;", (user_id,))
            conn.commit()

    def list_users(self) -> list[str]:
        """
        List all users with memories.
        
        Returns:
            List of user IDs
        """
        with sqlite3.connect(self.db_path) as conn:
            results = conn.execute("SELECT user_id FROM memory;").fetchall()
            return [row[0] for row in results]


def create_memory_tool(
    memory_store: LongTermMemory, 
    user_id: str, 
    llm: Optional[ChatAnthropic] = None
) -> tool:
    """
    Create a LangChain tool for updating memory.
    
    This tool can be used by ReAct agents to update the user's long-term memory.
    
    Args:
        memory_store: The memory storage instance
        user_id: The user whose memory to update
        llm: Language model for merging memories (defaults to claude-sonnet-4)
        
    Returns:
        A LangChain tool that can be used by agents
    """
    llm = llm or ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
    
    @tool
    async def update_memory(new_information: str) -> str:
        """Update the user's long-term memory with new information.
        
        Use this tool when the user shares personal information, preferences,
        or stable facts that should be remembered for future conversations.
        
        Args:
            new_information: Any information that should be added or updated in the system's memory
            
        Returns:
            Confirmation that the memory was updated
        """
        # Get current memory
        existing_memory = memory_store.read(user_id)
        
        # Use LLM to intelligently merge memories
        prompt = format_update_prompt(existing_memory, new_information)
        response = await llm.ainvoke(prompt)
        updated_memory = response.content.strip()
        
        # Save updated memory
        memory_store.write(user_id, updated_memory)
        
        # Return confirmation
        preview = updated_memory[:100] + "..." if len(updated_memory) > 100 else updated_memory
        return f"Memory updated successfully. Current memory: {preview}"
    
    return update_memory