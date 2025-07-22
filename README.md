# Long-Term Memory for Chatbots

A simple system that gives chatbots persistent memory across conversations.

## Quick Start

```bash
# Install
poetry install

# Set API key
export ANTHROPIC_API_KEY="your-key"

# Run tests
poetry run pytest

# Run CLI (after poetry install)
poetry run ltm

# Run API server
poetry run ltm-api

# Or run example
poetry run python example.py
```

## How It Works

1. **Memory Storage** (`memory.py`) - SQLite database with one text string per user
2. **ReAct Agent** (`agent.py`) - Uses Claude to autonomously decide what to remember
3. **Interfaces** (`cli.py`, `api.py`) - Ways to interact with the system

The agent:
- Sees the user's current memory in every message
- Has access to an `update_memory` tool
- Decides on its own when something is worth saving (no heuristics!)
- Intelligently merges new information with existing memories

## Core Components

### Memory Storage
```python
from memory import LongTermMemory

memory = LongTermMemory()
memory.write("alice", "Likes hiking and has a dog named Max")
print(memory.read("alice"))  # "Likes hiking and has a dog named Max"
```

### Chat Agent
```python
from agent import MemoryAgent

agent = MemoryAgent("alice")
response = agent.chat_sync("My birthday is in June")
# Memory is automatically updated if the agent deems it important
```

## Project Structure

```
simple_ltm/
├── src/simple_ltm/     # Main package
│   ├── memory.py       # Database operations
│   ├── agent.py        # ReAct agent
│   ├── cli.py          # Command-line interface
│   ├── api.py          # REST API
│   └── prompts.py      # Prompt templates
├── tests/              # End-to-end tests
│   └── test_e2e.py     # Comprehensive test suite
└── example.py          # Usage example
```

## Key Concepts

- **Persistent Memory**: Survives between conversations
- **Intelligent Merging**: New info is merged with existing memory, not overwritten
- **Multi-User**: Each user has their own memory space
- **Automatic**: Agent decides what's worth remembering

## Requirements

- Python 3.9+
- Anthropic API key for Claude
- Poetry for dependency management