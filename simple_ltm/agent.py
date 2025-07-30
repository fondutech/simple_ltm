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
import json
from typing import Annotated, Optional, Sequence, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from memory import LongTermMemory, create_memory_tool
from prompts import format_agent_system_prompt




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
        self.tools_by_name = {t.name: t for t in self.tools}
        
        # Bind tools to model
        self.model_with_tools = self.llm.bind_tools(self.tools)
        
        # Define state
        class AgentState(TypedDict):
            messages: Annotated[Sequence[BaseMessage], add_messages]
        
        # Build graph
        builder = StateGraph(AgentState)
        builder.add_node("agent", self._call_model)
        builder.add_node("tools", self._tool_node)
        builder.set_entry_point("agent")
        builder.add_conditional_edges(
            "agent", 
            self._should_continue,
            {"continue": "tools", "end": END}
        )
        builder.add_edge("tools", "agent")
        
        self.agent = builder.compile()
        
    async def _call_model(self, state, cfg: RunnableConfig = None):
        """Call the LLM with current state."""
        # Get current memory and create system message
        current_memory = self.memory_store.read(self.user_id)
        system = SystemMessage(content=format_agent_system_prompt(existing_user_memory=current_memory))
        
        # Invoke model with system message + conversation
        messages = [system] + state["messages"]
        response = await self.model_with_tools.ainvoke(messages, cfg)
        return {"messages": [response]}
    
    async def _tool_node(self, state):
        """Execute tool calls from the last message."""
        results = []
        for tool_call in state["messages"][-1].tool_calls:
            if tool_call["name"] in self.tools_by_name:
                result = await self.tools_by_name[tool_call["name"]].ainvoke(tool_call["args"])
                results.append(
                    ToolMessage(
                        content=json.dumps(result) if not isinstance(result, str) else result,
                        tool_call_id=tool_call["id"]
                    )
                )
        return {"messages": results}
    
    def _should_continue(self, state):
        """Determine if we should continue to tools or end."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
        return "end"
    
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
        
        # Run the ReAct agent with conversation history
        # Note: System message is created in _call_model with current memory
        result = await self.agent.ainvoke({"messages": self.conversation_history})
        
        # Update conversation history with new messages
        # (The graph already includes our input message)
        self.conversation_history = result["messages"]
        
        # Return the final assistant response
        return result["messages"][-1].content
    
    def chat_sync(self, message: str) -> str:
        """Synchronous version of chat for convenience."""
        return asyncio.run(self.chat(message))