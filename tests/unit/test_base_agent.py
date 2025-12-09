"""
Unit tests for BaseAgent class.

Tests the common initialization logic for all agents including:
- API key validation
- LLM initialization
- Mock mode handling
- Logging setup
"""
import pytest
from unittest.mock import MagicMock, patch
from src.agents.base_agent import BaseAgent
from src.core.config import settings


class ConcreteAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""
    
    def _setup(self):
        """Minimal setup for testing."""
        self.setup_called = True


class TestBaseAgent:
    """Test suite for BaseAgent class."""
    
    @patch('src.agents.base_agent.ChatGoogleGenerativeAI')
    def test_init_with_real_llm(self, mock_llm_class):
        """Test initialization in real mode with LLM."""
        # Setup
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        
        with patch.object(settings, 'USE_REAL_LLM', True):
            with patch.object(settings, 'GEMINI_API_KEY', 'test_key'):
                # Execute
                agent = ConcreteAgent(
                    agent_name="TestAgent",
                    temperature=0.8,
                    max_retries=5,
                    request_timeout=60.0
                )
                
                # Verify
                assert agent.agent_name == "TestAgent"
                assert agent.mock_mode is False
                assert agent.llm is not None
                assert agent.setup_called is True
                
                # Verify LLM was initialized with correct parameters
                mock_llm_class.assert_called_once_with(
                    model=settings.llm_model_name,
                    google_api_key='test_key',
                    temperature=0.8,
                    max_retries=5,
                    request_timeout=60.0
                )
    
    def test_init_in_mock_mode(self):
        """Test initialization in mock mode."""
        with patch.object(settings, 'USE_REAL_LLM', False):
            # Execute
            agent = ConcreteAgent(
                agent_name="TestAgent"
            )
            
            # Verify
            assert agent.agent_name == "TestAgent"
            assert agent.mock_mode is True
            assert agent.llm is None
            assert agent.setup_called is True
    
    @patch('src.agents.base_agent.ChatGoogleGenerativeAI')
    def test_init_without_llm_requirement(self, mock_llm_class):
        """Test initialization for agents that don't require LLM."""
        with patch.object(settings, 'USE_REAL_LLM', True):
            with patch.object(settings, 'GEMINI_API_KEY', 'test_key'):
                # Execute
                agent = ConcreteAgent(
                    agent_name="TestAgent",
                    require_llm=False
                )
                
                # Verify
                assert agent.llm is None
                assert agent.setup_called is True
                # LLM should not be initialized
                mock_llm_class.assert_not_called()
    
    def test_init_missing_api_key_raises_error(self):
        """Test that missing API key raises ValueError in real mode."""
        with patch.object(settings, 'USE_REAL_LLM', True):
            with patch.object(settings, 'GEMINI_API_KEY', None):
                # Execute & Verify
                with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
                    ConcreteAgent(agent_name="TestAgent")
    
    @patch('src.agents.base_agent.ChatGoogleGenerativeAI')
    def test_default_parameters(self, mock_llm_class):
        """Test that default parameters are applied correctly."""
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        
        with patch.object(settings, 'USE_REAL_LLM', True):
            with patch.object(settings, 'GEMINI_API_KEY', 'test_key'):
                # Execute
                agent = ConcreteAgent(agent_name="TestAgent")
                
                # Verify default parameters were used
                mock_llm_class.assert_called_once()
                call_kwargs = mock_llm_class.call_args[1]
                assert call_kwargs['temperature'] == 0.7
                assert call_kwargs['max_retries'] == 3
                assert call_kwargs['request_timeout'] == 30.0
    
    def test_setup_hook_is_called(self):
        """Test that _setup hook is called during initialization."""
        with patch.object(settings, 'USE_REAL_LLM', False):
            agent = ConcreteAgent(agent_name="TestAgent")
            
            # Verify _setup was called
            assert hasattr(agent, 'setup_called')
            assert agent.setup_called is True
    
    @patch('src.agents.base_agent.ChatGoogleGenerativeAI')
    def test_custom_temperature(self, mock_llm_class):
        """Test custom temperature parameter."""
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        
        with patch.object(settings, 'USE_REAL_LLM', True):
            with patch.object(settings, 'GEMINI_API_KEY', 'test_key'):
                # Execute with custom temperature
                agent = ConcreteAgent(
                    agent_name="TestAgent",
                    temperature=0.9
                )
                
                # Verify
                call_kwargs = mock_llm_class.call_args[1]
                assert call_kwargs['temperature'] == 0.9


class TestAbstractMethods:
    """Test that BaseAgent enforces abstract methods."""
    
    def test_cannot_instantiate_base_agent_directly(self):
        """Test that BaseAgent cannot be instantiated without implementing _setup."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseAgent(agent_name="TestAgent")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
