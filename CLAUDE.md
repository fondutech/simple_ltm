# Claude Development Notes

## Project Overview

This is a teaching example demonstrating how simple string-based memory can power sophisticated AI applications. It shows that effective long-term memory doesn't require vector databases, embeddings, or complex retrieval - just two strings and intelligent merging.

## Key Design Decisions

1. **ReAct Pattern**: The agent has access to an `update_memory` tool and decides when to use it
2. **One String Per User**: Simple SQLite storage with intelligent merging
3. **No Heuristics**: The LLM decides what's memorable, not coded rules

## Running Tests

Tests require an Anthropic API key. You have two options:

### Option 1: Export directly
```bash
export ANTHROPIC_API_KEY="your-key-here"
poetry run pytest
```

### Option 2: Use set_secrets.sh (gitignored)
Create a `set_secrets.sh` file in the project root:
```bash
#!/bin/bash
export ANTHROPIC_API_KEY="your-key-here"
```

Then run tests with:
```bash
source set_secrets.sh && poetry run pytest
```

## Development Commands

```bash
# Run the Chainlit web app
chainlit run src/simple_ltm/app.py

# Run specific test categories
poetry run pytest -k TestMemoryStorage  # Just storage tests
poetry run pytest -k test_agent         # Just agent tests (need API key)
```

## Architecture Notes

- `src/simple_ltm/memory.py` - Core SQLite storage, very simple CRUD
- `src/simple_ltm/agent.py` - ReAct agent using LangGraph StateGraph
- `src/simple_ltm/app.py` - Modern web UI with Chainlit
- `src/simple_ltm/prompts.py` - Clean, simple prompts
- `src/simple_ltm/meta_prompts.py` - Agent behavior instructions
- Tests validate the agent's autonomous decision-making

The system is intentionally simple - complexity comes from Claude's intelligence, not the code.

## Recent Updates

- **Chainlit Web UI**: Modern web interface with ChatGPT-style UI
- **Memory sidebar**: See memory updates in real-time
- **Tool tracing**: Expandable view of agent actions
- **Model**: Uses Claude Sonnet 4 (claude-sonnet-4-20250514) by default