"""
agent.py
========

ReAct-based chatbot agent with long-term memory capabilities.

The agent uses the ReAct pattern:
- Sees the user's message and current memory
- Reasons about whether to update memory
- Acts by calling the update_memory tool when appropriate

No heuristics - the agent decides autonomously what's worth remembering!
"""

import asyncio
from typing import List, Optional

from typing import Annotated, Sequence, TypedDict
import json

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent

from .memory import LongTermMemory, create_memory_tool
from .prompts import AGENT_SYSTEM_TEMPLATE




class MemoryAgent:
    """
    A ReAct agent with long-term memory capabilities.
    
    The agent can autonomously decide when to update the user's memory
    based on the conversation.
    """
    
    def __init__(
        self, 
        user_id: str,
        memory_store: Optional[LongTermMemory] = None,
        llm: Optional[ChatAnthropic] = None,
        db_path: str = "memory.db"
    ):
        """
        Initialize the memory agent.
        
        Args:
            user_id: Unique identifier for the user
            memory_store: Memory storage instance (creates new if None)
            llm: Language model to use (defaults to claude-sonnet-4)
            db_path: Path to database if creating new memory store
        """
        self.user_id = user_id
        self.memory_store = memory_store or LongTermMemory(db_path)
        self.llm = llm or ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
        self.conversation_history: List[BaseMessage] = []
        self._build_agent()
    
    def clear_conversation(self):
        """Clear the conversation history while preserving long-term memory."""
        self.conversation_history = []
    
    def _build_agent(self):
        """Build the ReAct agent graph."""
        # Create memory tool
        self.update_memory_tool = create_memory_tool(self.memory_store, self.user_id, self.llm)
        self.tools = [self.update_memory_tool]
        self.model_with_tools = self.llm.bind_tools(self.tools)
        self.agent = create_react_agent(model=self.model_with_tools, tools=self.tools)
        
    async def _call_model(self, state, cfg: RunnableConfig = None):
        """Call the LLM with current state."""
        # Get current memory and create system message
        current_memory = self.memory_store.read(self.user_id)
        system = SystemMessage(content=AGENT_SYSTEM_TEMPLATE.format(user_memory=current_memory))
        
        # Invoke model with system message + conversation
        messages = [system] + state["messages"]
        response = await self.model_with_tools.ainvoke(messages, cfg)
        return {"messages": [response]}
    
    async def chat(self, message: str) -> str:
        """
        Send a message to the agent and get a response.
        
        Args:
            message: The user's message
            
        Returns:
            The agent's response
        """
        # Add user message to history
        self.conversation_history.append(HumanMessage(content=message))
        
        # Create system message with current memory
        current_memory = self.memory_store.read(self.user_id)
        system_msg = SystemMessage(
            content=AGENT_SYSTEM_TEMPLATE.format(user_memory=current_memory)
        )
        
        # Run the ReAct agent with conversation history
        result = await self.agent.ainvoke({"messages": self.conversation_history})
        
        # Update conversation history with new messages
        # (The graph already includes our input message)
        self.conversation_history = result["messages"]
        
        # Return the final assistant response
        return result["messages"][-1].content
    
    def chat_sync(self, message: str) -> str:
        """Synchronous version of chat for convenience."""
        return asyncio.run(self.chat(message))


def demo():
    """Interactive demo of the memory agent."""
    user_id = input("Enter your user ID (or press Enter for 'default'): ").strip()
    if not user_id:
        user_id = "default"
    
    agent = MemoryAgent(user_id)
    print(f"\nStarting conversation for user: {user_id}")
    print("Type 'exit' to quit, 'memory' to see your current memory\n")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() == "exit":
            break
        elif user_input.lower() == "memory":
            memory = agent.memory_store.read(user_id)
            print(f"Current memory: {memory if memory else '(empty)'}")
            continue
        
        response = agent.chat_sync(user_input)
        print(f"Assistant: {response}\n")


if __name__ == "__main__":
    demo()