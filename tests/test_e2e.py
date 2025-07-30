"""
End-to-end tests for the Long-Term Memory system.

These tests verify the complete workflow from user input to memory persistence.
"""

import asyncio
import os
import tempfile
from pathlib import Path

import pytest
from langchain_anthropic import ChatAnthropic

import sys
sys.path.insert(0, 'simple_ltm')
from memory import LongTermMemory
from agent import MemoryAgent


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if Path(db_path).exists():
        Path(db_path).unlink()


@pytest.fixture
def memory_store(temp_db):
    """Create a memory store with temporary database."""
    return LongTermMemory(temp_db)


@pytest.fixture
def mock_llm(monkeypatch):
    """Mock LLM for tests that don't need real API calls."""
    class MockLLM:
        async def ainvoke(self, messages):
            # Simple mock that always returns a response
            class MockResponse:
                content = "Test response"
            return MockResponse()
    
    return MockLLM()


class TestMemoryStorage:
    """Test the core memory storage functionality."""
    
    def test_create_read_memory(self, memory_store):
        """Test basic CRUD operations."""
        # Initially empty
        assert memory_store.read("test_user") == ""
        
        # Write memory
        memory_store.write("test_user", "Likes pizza and coding")
        assert memory_store.read("test_user") == "Likes pizza and coding"
        
        # Update memory
        memory_store.write("test_user", "Likes pizza, coding, and hiking")
        assert memory_store.read("test_user") == "Likes pizza, coding, and hiking"
    
    def test_multiple_users(self, memory_store):
        """Test that different users have separate memories."""
        memory_store.write("alice", "Loves hiking")
        memory_store.write("bob", "Enjoys cooking")
        
        assert memory_store.read("alice") == "Loves hiking"
        assert memory_store.read("bob") == "Enjoys cooking"
        assert memory_store.read("charlie") == ""
    
    def test_list_users(self, memory_store):
        """Test listing all users."""
        assert memory_store.list_users() == []
        
        memory_store.write("alice", "Memory 1")
        memory_store.write("bob", "Memory 2")
        
        users = memory_store.list_users()
        assert len(users) == 2
        assert "alice" in users
        assert "bob" in users
    
    def test_delete_memory(self, memory_store):
        """Test memory deletion."""
        memory_store.write("alice", "Test memory")
        assert memory_store.read("alice") == "Test memory"
        
        memory_store.delete("alice")
        assert memory_store.read("alice") == ""
        assert "alice" not in memory_store.list_users()


@pytest.mark.asyncio
class TestMemoryAgent:
    """Test the ReAct agent with memory capabilities."""
    
    @pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), 
                        reason="Requires ANTHROPIC_API_KEY")
    async def test_agent_remembers_information(self, temp_db):
        """Test that agent correctly saves important information."""
        agent = MemoryAgent("test_user", db_path=temp_db)
        memory_store = LongTermMemory(temp_db)
        
        # Tell the agent something memorable
        response = await agent.chat("My name is Alice and I have a cat named Whiskers")
        assert response  # Should get some response
        
        # Wait a bit for memory update
        await asyncio.sleep(1)
        
        # Check if memory was updated
        memory = memory_store.read("test_user")
        assert "Alice" in memory or "alice" in memory.lower()
        assert "cat" in memory.lower()
        # The agent might save "Whiskers" or might not - it decides
    
    @pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), 
                        reason="Requires ANTHROPIC_API_KEY")
    async def test_agent_uses_memory_in_responses(self, temp_db):
        """Test that agent uses stored memory to answer questions."""
        agent = MemoryAgent("test_user", db_path=temp_db)
        
        # First conversation - share information
        await agent.chat("My favorite color is blue and I work as a teacher")
        await asyncio.sleep(1)  # Wait for memory update
        
        # New conversation - agent should remember
        agent.clear_conversation()
        response = await agent.chat("What do you remember about me?")
        
        # Agent should mention something from memory
        response_lower = response.lower()
        assert "blue" in response_lower or "teacher" in response_lower
    
    @pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), 
                        reason="Requires ANTHROPIC_API_KEY")
    async def test_conversation_history_maintained(self, temp_db):
        """Test that conversation history is maintained within a session."""
        agent = MemoryAgent("test_user", db_path=temp_db)
        
        # Have a conversation
        await agent.chat("I'm planning a trip to Japan")
        response = await agent.chat("What should I pack?")
        
        # Response should be contextual to Japan trip
        assert "Japan" in response or "travel" in response.lower()
    
    async def test_clear_conversation(self, temp_db):
        """Test that clear_conversation resets history but not memory."""
        agent = MemoryAgent("test_user", db_path=temp_db)
        memory_store = LongTermMemory(temp_db)
        
        # Pre-populate memory
        memory_store.write("test_user", "Likes hiking and has a dog")
        
        # Have a conversation
        agent.conversation_history.append("test message")
        assert len(agent.conversation_history) > 0
        
        # Clear conversation
        agent.clear_conversation()
        assert len(agent.conversation_history) == 0
        
        # Memory should still exist
        assert memory_store.read("test_user") == "Likes hiking and has a dog"


@pytest.mark.asyncio
class TestEndToEnd:
    """Complete end-to-end scenarios."""
    
    @pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), 
                        reason="Requires ANTHROPIC_API_KEY")
    async def test_multi_user_scenario(self, temp_db):
        """Test complete scenario with multiple users."""
        memory_store = LongTermMemory(temp_db)
        
        # Alice's conversation
        alice = MemoryAgent("alice", db_path=temp_db)
        await alice.chat("I'm Alice, I love photography and have two cats")
        await asyncio.sleep(1)
        
        # Bob's conversation
        bob = MemoryAgent("bob", db_path=temp_db)
        await bob.chat("I'm Bob, I enjoy cooking Italian food")
        await asyncio.sleep(1)
        
        # Verify memories are separate
        alice_memory = memory_store.read("alice")
        bob_memory = memory_store.read("bob")
        
        assert alice_memory != bob_memory
        assert "photograph" in alice_memory.lower() or "cat" in alice_memory.lower()
        assert "cooking" in bob_memory.lower() or "italian" in bob_memory.lower()
        
        # New conversation with Alice - should remember her info
        alice_new = MemoryAgent("alice", db_path=temp_db)
        response = await alice_new.chat("Do you know what my hobbies are?")
        assert "photograph" in response.lower() or "cat" in response.lower()
    
    @pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), 
                        reason="Requires ANTHROPIC_API_KEY")
    async def test_memory_evolution(self, temp_db):
        """Test how memory evolves over multiple conversations."""
        agent = MemoryAgent("evolving_user", db_path=temp_db)
        memory_store = LongTermMemory(temp_db)
        
        # First fact
        await agent.chat("I have a dog named Max")
        await asyncio.sleep(1)
        memory1 = memory_store.read("evolving_user")
        
        # Additional fact
        await agent.chat("I also have a cat named Luna")
        await asyncio.sleep(1)
        memory2 = memory_store.read("evolving_user")
        
        # Memory should contain both pets
        assert "Max" in memory2 or "dog" in memory2.lower()
        assert "Luna" in memory2 or "cat" in memory2.lower()
        
        # Update existing fact
        await agent.chat("Actually, I have two dogs now - Max and Rex")
        await asyncio.sleep(1)
        memory3 = memory_store.read("evolving_user")
        
        # Should reflect the update
        assert "two dogs" in memory3.lower() or "rex" in memory3.lower()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])