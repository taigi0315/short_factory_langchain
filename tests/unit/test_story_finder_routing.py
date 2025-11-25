import unittest
from unittest.mock import MagicMock, patch
import os

# Set dummy env vars before importing to avoid validation errors if possible,
# but since we import settings from src.core.config, we might need to patch settings.
from src.agents.story_finder.agent import StoryFinderAgent
from src.agents.story_finder.prompts import (
    NEWS_PROMPT, REAL_STORY_PROMPT, EDUCATIONAL_PROMPT, 
    FICTION_PROMPT, DEFAULT_PROMPT
)
from langchain_core.messages import AIMessage

from langchain_core.runnables import RunnableLambda

class TestStoryFinderRouting(unittest.TestCase):
    
    def setUp(self):
        # Setup common mocks
        self.mock_llm_patcher = patch('src.agents.story_finder.agent.ChatGoogleGenerativeAI')
        self.mock_tavily_patcher = patch('src.agents.story_finder.agent.TavilySearchResults')
        self.mock_settings_patcher = patch('src.agents.story_finder.agent.settings')
        
        self.mock_llm_class = self.mock_llm_patcher.start()
        self.mock_tavily_class = self.mock_tavily_patcher.start()
        self.mock_settings = self.mock_settings_patcher.start()
        
        # Configure settings to force "Real LLM" mode logic
        self.mock_settings.USE_REAL_LLM = True
        self.mock_settings.GEMINI_API_KEY = "dummy_key"
        self.mock_settings.TAVILY_API_KEY = "dummy_tavily_key"
        self.mock_settings.llm_model_name = "gemini-pro"
        
        # Setup instances
        self.mock_llm_instance = MagicMock()
        # Wrap in RunnableLambda so it supports | operator
        self.mock_llm_class.return_value = RunnableLambda(self.mock_llm_instance)
        
        self.mock_search_tool_instance = MagicMock()
        self.mock_tavily_class.return_value = self.mock_search_tool_instance
        self.mock_search_tool_instance.invoke.return_value = "Mock Search Results"
        
        # Default valid response
        self.valid_response_content = """
        {
            "stories": [
                {
                    "title": "Story",
                    "summary": "Summary",
                    "hook": "Hook",
                    "keywords": ["test"],
                    "category": "test",
                    "mood": "neutral"
                }
            ]
        }
        """
        self.mock_llm_instance.return_value = AIMessage(content=self.valid_response_content)

    def tearDown(self):
        self.mock_llm_patcher.stop()
        self.mock_tavily_patcher.stop()
        self.mock_settings_patcher.stop()

    def test_news_category_triggers_search(self):
        """Test that NEWS category triggers search and uses correct prompt."""
        agent = StoryFinderAgent()
        
        inputs = {
            "subject": "Test Subject",
            "num_stories": 3,
            "category": "news",
            "mood": "neutral"
        }
        
        agent.chain.invoke(inputs)
        
        # Verify Search was called
        self.mock_search_tool_instance.invoke.assert_called()
        args, _ = self.mock_search_tool_instance.invoke.call_args
        self.assertIn("Test Subject", args[0])
        self.assertIn("news", args[0])
        
    def test_fiction_category_skips_search(self):
        """Test that FICTION category does NOT trigger search."""
        agent = StoryFinderAgent()
        
        inputs = {
            "subject": "Test Subject",
            "num_stories": 3,
            "category": "fiction",
            "mood": "neutral"
        }
        
        agent.chain.invoke(inputs)
            
        # Verify Search was NOT called
        self.mock_search_tool_instance.invoke.assert_not_called()

    def test_real_story_category_triggers_search(self):
        """Test that REAL_STORY category triggers search."""
        agent = StoryFinderAgent()
        
        inputs = {
            "subject": "Test Subject",
            "num_stories": 3,
            "category": "real_story",
            "mood": "neutral"
        }
        
        agent.chain.invoke(inputs)
            
        self.mock_search_tool_instance.invoke.assert_called()

    def test_educational_category_search_behavior(self):
        """Test EDUCATIONAL category search behavior (Default: No search)."""
        agent = StoryFinderAgent()
        
        inputs = {
            "subject": "Test Subject",
            "num_stories": 3,
            "category": "educational",
            "mood": "neutral"
        }
        
        agent.chain.invoke(inputs)
            
        # Should NOT search now
        self.mock_search_tool_instance.invoke.assert_not_called()

if __name__ == '__main__':
    unittest.main()
