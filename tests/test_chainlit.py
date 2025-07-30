"""
Tests for Chainlit integration.

These tests verify the Chainlit UI components work correctly with the memory agent.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import chainlit as cl

# Import our app handlers
from simple_ltm.app import start, handle_message, clear_memory


@pytest.fixture
def mock_user_session():
    """Mock Chainlit user session."""
    session = {}
    
    def get(key, default=None):
        return session.get(key, default)
    
    def set(key, value):
        session[key] = value
    
    mock = Mock()
    mock.get = get
    mock.set = set
    return mock


@pytest.fixture
def mock_message():
    """Mock Chainlit message."""
    async def send():
        return None
    
    msg = Mock()
    msg.send = AsyncMock()
    msg.content = ""
    msg.author = "User"
    return msg


@pytest.mark.asyncio
class TestChainlitHandlers:
    """Test Chainlit event handlers."""
    
    async def test_on_chat_start_with_api_key(self, mock_user_session, mock_message, monkeypatch):
        """Test chat start handler with valid API key."""
        # Set API key
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("USER_ID", "test_user")
        
        # Mock Chainlit components
        with patch('chainlit.user_session', mock_user_session), \
             patch('chainlit.Message', return_value=mock_message):
            
            # Run start handler
            await start()
            
            # Verify agent was created and stored
            agent = mock_user_session.get("agent")
            assert agent is not None
            assert agent.user_id == "test_user"
            
            # Verify welcome message was sent
            assert mock_message.send.called
    
    async def test_on_chat_start_without_api_key(self, mock_user_session, mock_message, monkeypatch):
        """Test chat start handler without API key."""
        # Clear API key
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        
        # Mock Chainlit components
        with patch('chainlit.user_session', mock_user_session), \
             patch('chainlit.Message', return_value=mock_message):
            
            # Run start handler
            await start()
            
            # Verify error message was sent
            assert mock_message.send.called
            # Verify agent was NOT created
            assert mock_user_session.get("agent") is None
    
    async def test_handle_message_with_agent(self, mock_user_session, mock_message):
        """Test message handler with valid agent."""
        # Create mock agent
        mock_agent = Mock()
        mock_agent.chat = AsyncMock(return_value="Test response")
        mock_user_session.set("agent", mock_agent)
        
        # Create input message
        input_msg = Mock()
        input_msg.content = "Hello"
        
        # Mock Chainlit components
        with patch('chainlit.user_session', mock_user_session), \
             patch('chainlit.Message', return_value=mock_message):
            
            # Handle message
            await handle_message(input_msg)
            
            # Verify agent was called
            mock_agent.chat.assert_called_once_with("Hello")
            
            # Verify response was sent
            assert mock_message.send.called
    
    async def test_handle_message_without_agent(self, mock_user_session, mock_message):
        """Test message handler without agent (expired session)."""
        # No agent in session
        input_msg = Mock()
        input_msg.content = "Hello"
        
        # Mock Chainlit components
        with patch('chainlit.user_session', mock_user_session), \
             patch('chainlit.Message', return_value=mock_message):
            
            # Handle message
            await handle_message(input_msg)
            
            # Verify error message was sent
            assert mock_message.send.called
    
    async def test_clear_memory_action(self, mock_message):
        """Test memory clear action callback."""
        # Create mock action
        mock_action = Mock()
        mock_action.remove = AsyncMock()
        
        # Mock memory store
        with patch('simple_ltm.app.memory_store') as mock_store, \
             patch('simple_ltm.app.USER_ID', 'test_user'), \
             patch('chainlit.Message', return_value=mock_message):
            
            # Run clear memory action
            await clear_memory(mock_action)
            
            # Verify memory was cleared
            mock_store.write.assert_called_once_with('test_user', '')
            
            # Verify confirmation message
            assert mock_message.send.called
            
            # Verify action was removed
            mock_action.remove.assert_called_once()


class TestChainlitIntegration:
    """Test full Chainlit integration scenarios."""
    
    def test_app_imports(self):
        """Test that all required imports work."""
        from simple_ltm import app
        assert hasattr(app, 'start')
        assert hasattr(app, 'handle_message')
        assert hasattr(app, 'clear_memory')
    
    def test_memory_persistence(self, tmp_path):
        """Test that memory persists across sessions."""
        # This would require a more complex integration test
        # with actual Chainlit test client
        pass