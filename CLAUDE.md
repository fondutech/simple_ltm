# Claude Development Notes

## Project Overview

This is a long-term memory system for chatbots that allows them to remember information across conversations. The agent uses Claude (Anthropic) to autonomously decide what information is worth remembering - no heuristics or rules, just intelligent decision-making.

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
# Run CLI
poetry run ltm

# Run API server  
poetry run ltm-api

# Run specific test categories
poetry run pytest -k TestMemoryStorage  # Just storage tests
poetry run pytest -k test_agent         # Just agent tests (need API key)
```

## Architecture Notes

- `src/simple_ltm/memory.py` - Core SQLite storage, very simple CRUD
- `src/simple_ltm/agent.py` - ReAct agent using `create_react_agent` 
- `src/simple_ltm/prompts.py` - Clean, simple prompts
- Tests validate the agent's autonomous decision-making

The system is intentionally simple - complexity comes from Claude's intelligence, not the code.