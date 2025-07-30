# Simple Long-Term Memory

A teaching example showing how two strings and an LLM can create a powerful memory system for AI assistants.

## The Core Idea

```python
# That's it. Two strings in, one string out.
existing_memory = "I have a dog named Max"
new_info = "My dog Max is 5 years old"
merged_memory = llm.merge(existing_memory, new_info)
# Result: "I have a dog named Max who is 5 years old [recorded:2025-01-30]"
```

No vector databases. No embeddings. No retrieval algorithms. Just intelligent text merging.

## Quick Start

```bash
# Install
poetry install

# Set API key
export ANTHROPIC_API_KEY="your-key"

# Run the web UI
chainlit run src/simple_ltm/app.py
```

## How It Works

1. User shares information with the AI assistant
2. Assistant decides if it's worth remembering (using a ReAct agent)
3. New info is merged with existing memory via LLM
4. Memory persists across conversations

The entire implementation is ~500 lines of Python.

## Example Usage

```python
from simple_ltm import MemoryAgent

agent = MemoryAgent("alice")

# First conversation
await agent.chat("I'm learning Spanish for my trip to Barcelona")
# Memory: "I'm learning Spanish for a trip to Barcelona [recorded:2025-01-30]"

# New conversation
await agent.chat("What was I learning?")
# Agent recalls the Spanish learning goal
```

## Key Features

- **Temporal markers** - Tracks when information was recorded: `[recorded:2025-01-30]`
- **First-person storage** - "I have a dog" not "User has a dog"  
- **Intelligent merging** - LLM resolves conflicts and maintains coherence
- **User switching** - Built-in support for multiple users

## Architecture

```
simple_ltm/
├── memory.py       # SQLite storage (create, read, update, delete)
├── agent.py        # ReAct agent with memory tool
├── prompts.py      # Instructions for memory merging
└── app.py          # Chainlit web interface
```

## Insights

1. **LLMs are excellent at text merging** - They understand context and maintain coherence
2. **Timestamps matter** - Simple markers like `[recorded:2025-01-30]` provide crucial context
3. **Simple beats complex** - For many use cases, one string is all you need

## Testing

```bash
# Test storage
poetry run pytest -k TestMemoryStorage

# Test agent (needs API key)
poetry run pytest -k TestMemoryAgent
```

## Extending

- Swap Claude for any LLM
- Replace SQLite with any database  
- Customize prompts for your domain
- Add structured sections (JSON, markdown headers)

## When to Use This

✅ Personal assistants, coaching apps, customer service bots  
❌ Large knowledge bases, document retrieval systems

The power is in the simplicity. Sometimes two strings is all you need.

## License

MIT