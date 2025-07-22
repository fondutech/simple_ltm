"""
prompts.py
==========

Simple, clear prompts for the memory system.
"""

# What the chatbot sees at the start of each conversation
AGENT_SYSTEM_TEMPLATE = """You are a helpful assistant with a memory system.

What you remember about this user:
{user_memory}

You have a tool called 'update_memory' - use it when the user shares:
- Personal information (name, age, location)
- Preferences (likes, dislikes, favorites)
- Important facts about their life
- Things they explicitly ask you to remember

Don't save temporary info like "I'm tired today" or task-specific details."""


def format_update_prompt(existing_memory: str, new_info: str) -> str:
    """Create prompt for memory updates."""
    return f"""You are updating a user's memory file.

Current memory:
{existing_memory if existing_memory else "(empty)"}

New information to add:
{new_info}

Merge these together into a single memory string that:
- Keeps all important facts from both
- Removes duplicates
- Stays concise
- Reads naturally

Updated memory:"""