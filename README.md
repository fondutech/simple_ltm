# Simple Long-Term Memory

A teaching example showing how two strings and an LLM can create a powerful memory system for AI assistants. This is an implementation of the first architecture described in the [Long Term Memory Fundamentals](Long%20Term%20Memory%20Fundamentals.pdf) slide deck from the Maven class "Building LLM Applications for Data Scientists and Software Engineers" by Hugo Bowne-Anderson and Stefan Krawczyk.

## The Core Idea

```python
# That's it. Two strings in, one string out.
existing_memory = "I have a dog named Max"
new_info = "My dog Max is 5 years old"
merged_memory = llm.merge(existing_memory, new_info)
# Result: "I have a dog named Max who is 5 years old [recorded:2025-01-30]"
```

No vector databases. No embeddings. No retrieval algorithms. Just intelligent text merging.

## Background

This implementation demonstrates the "Single String Memory" architecture from the Long Term Memory Fundamentals slides - the simplest possible approach where:
- Each user's entire memory is one text string
- The LLM decides what to remember
- New information is merged with existing memory
- Everything fits in the context window

## Prerequisites

- Python 3.9-3.12 (3.13 not yet supported due to Chainlit compatibility)
- Poetry ([install instructions](https://python-poetry.org/docs/#installation))
- An Anthropic API key ([get one here](https://console.anthropic.com/))

## Quick Start

```bash
# Clone the repository
git clone https://github.com/fondutech/simple_ltm.git
cd simple_ltm

# Install dependencies
poetry install

# Set API key
export ANTHROPIC_API_KEY="your-key"

# Run the web UI (from project root)
cd simple_ltm && poetry run chainlit run app.py
```

## How It Works

1. User shares information with the AI assistant
2. Assistant decides if it's worth remembering (using a ReAct agent)
3. New info is merged with existing memory via LLM
4. Memory persists across conversations

The entire implementation is ~600 lines of Python.

## Example Conversation

In the web UI:
```
User: I'm learning Spanish for my trip to Barcelona
Assistant: That's exciting! Learning Spanish for your Barcelona trip will definitely enhance your experience.
[Memory updated: I'm learning Spanish for a trip to Barcelona [recorded:2025-01-30]]

User: What was I learning?
Assistant: You're learning Spanish for your upcoming trip to Barcelona!
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
├── meta_prompts.py # System prompts and tool instructions
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

## Credits

- **Implementation**: Eddie Landesberg
- **Architecture Design**: Based on the Long Term Memory Fundamentals slides from the Maven class "Building LLM Applications for Data Scientists and Software Engineers" by Hugo Bowne-Anderson and Stefan Krawczyk

## License

MIT