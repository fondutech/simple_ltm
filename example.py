#!/usr/bin/env python3
"""
example.py
==========

Shows how the memory system works:
1. Agent decides what to remember (no heuristics!)
2. Memory persists across conversations
3. Each user has their own memory space
"""

import asyncio
import os
from src.simple_ltm import LongTermMemory, MemoryAgent


async def main():
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Please set ANTHROPIC_API_KEY environment variable")
        return
    
    print("🧠 Long-Term Memory Example\n")
    
    # Create a memory agent for "alice"
    agent = MemoryAgent("alice")
    memory_store = LongTermMemory()
    
    # First conversation
    print("=== First Conversation ===")
    print("Alice: Hi! My name is Alice and I love hiking")
    response = await agent.chat("Hi! My name is Alice and I love hiking")
    print(f"Bot: {response}\n")
    
    print("Alice: I have a dog named Max")
    response = await agent.chat("I have a dog named Max")
    print(f"Bot: {response}\n")
    
    # Show what the agent decided to save
    print("💾 Current memory:", memory_store.read("alice"))
    
    # New conversation (clear chat history but keep memory)
    print("\n=== New Conversation (memory persists) ===")
    agent.clear_conversation()
    
    print("Alice: Do you remember anything about me?")
    response = await agent.chat("Do you remember anything about me?")
    print(f"Bot: {response}\n")
    
    print("Alice: What's my dog's name?")
    response = await agent.chat("What's my dog's name?")
    print(f"Bot: {response}\n")
    
    # Show how different users have different memories
    print("=== Different User (Bob) ===")
    bob_agent = MemoryAgent("bob")
    
    print("Bob: Do you know anything about me?")
    response = await bob_agent.chat("Do you know anything about me?")
    print(f"Bot: {response}\n")
    
    print("📊 Memory Summary:")
    print(f"- Alice's memory: {memory_store.read('alice')}")
    print(f"- Bob's memory: {memory_store.read('bob') or '(empty)'}")


if __name__ == "__main__":
    asyncio.run(main())