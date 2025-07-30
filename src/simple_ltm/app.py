#!/usr/bin/env python3
"""
Chainlit app for the memory chatbot.

A modern web interface with:
- ChatGPT-style UI
- Memory sidebar
- User switching
- Tool call tracing
- Markdown support
"""

import os

import chainlit as cl

from simple_ltm.agent import MemoryAgent
from simple_ltm.memory import LongTermMemory


# Initialize memory store
memory_store = LongTermMemory()


@cl.on_chat_start
async def start():
    """Initialize the chat session."""
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        await cl.Message(
            content="⚠️ Missing ANTHROPIC_API_KEY environment variable. Please set it and restart.",
            author="System"
        ).send()
        return
    
    # Get user ID from environment or session
    user_id = os.getenv("USER_ID", "default")
    
    # Set up settings for user switching
    settings = await cl.ChatSettings(
        [
            cl.input_widget.TextInput(
                id="user_id",
                label="User ID",
                initial=user_id,
                description="Switch between different users"
            ),
        ]
    ).send()
    
    # Create agent for this session
    agent = MemoryAgent(user_id, memory_store)
    cl.user_session.set("agent", agent)
    cl.user_session.set("user_id", user_id)
    
    # Display current memory using a custom sidebar
    memory = memory_store.read(user_id)
    if memory:
        # Create a persistent element that acts as a sidebar
        await cl.Message(
            content=f"**Current Memory:**\n\n{memory}",
            author="📝 Memory",
            actions=[
                cl.Action(name="clear_memory", payload={"action": "clear"}, label="Clear all memories")
            ]
        ).send()
    
    # Send greeting
    await cl.Message(
        content=f"👋 Hi! I'm your assistant with long-term memory. I'll remember important details from our conversations.\n\nUser: **{user_id}**"
    ).send()


@cl.on_settings_update
async def handle_settings(settings):
    """Handle settings updates (user switching)."""
    new_user_id = settings.get("user_id", "default")
    current_user_id = cl.user_session.get("user_id")
    
    if new_user_id != current_user_id:
        # Switch user
        cl.user_session.set("user_id", new_user_id)
        
        # Create new agent for the new user
        agent = MemoryAgent(new_user_id, memory_store)
        cl.user_session.set("agent", agent)
        
        # Display new user's memory
        memory = memory_store.read(new_user_id)
        if memory:
            await cl.Message(
                content=f"**Current Memory:**\n\n{memory}",
                author="📝 Memory",
                actions=[
                    cl.Action(name="clear_memory", payload={"action": "clear"}, label="Clear all memories")
                ]
            ).send()
        else:
            await cl.Message(
                content="*No memories yet for this user*",
                author="📝 Memory"
            ).send()
        
        # Notify user of switch
        await cl.Message(
            content=f"✅ Switched to user: **{new_user_id}**",
            author="System"
        ).send()


@cl.on_message
async def handle_message(message: cl.Message):
    """Handle incoming messages."""
    agent = cl.user_session.get("agent")
    user_id = cl.user_session.get("user_id")
    
    if not agent:
        await cl.Message(
            content="⚠️ Session expired. Please refresh the page.",
            author="System"
        ).send()
        return
    
    # Get response from agent
    response = await agent.chat(message.content)
    
    # Send response
    await cl.Message(content=response).send()
    
    # Check if memory was updated and display if changed
    new_memory = memory_store.read(user_id)
    old_memory = cl.user_session.get("last_memory", "")
    
    if new_memory != old_memory:
        cl.user_session.set("last_memory", new_memory)
        await cl.Message(
            content=f"**Updated Memory:**\n\n{new_memory}",
            author="📝 Memory",
            actions=[
                cl.Action(name="clear_memory", payload={"action": "clear"}, label="Clear all memories")
            ]
        ).send()


@cl.action_callback("clear_memory")
async def clear_memory(action: cl.Action):
    """Handle memory clear action."""
    user_id = cl.user_session.get("user_id", "default")
    memory_store.write(user_id, "")
    cl.user_session.set("last_memory", "")
    
    await cl.Message(
        content="✅ Memory cleared",
        author="System"
    ).send()
    
    # Remove the action button
    await action.remove()


def main():
    """Entry point for the Chainlit app."""
    # This is called by poetry script, but chainlit run is the actual entry
    print("To run the Chainlit app, use: chainlit run src/simple_ltm/app.py")
    print("Or if installed: chainlit run -m simple_ltm.app")


if __name__ == "__main__":
    # When run directly, just print instructions
    main()