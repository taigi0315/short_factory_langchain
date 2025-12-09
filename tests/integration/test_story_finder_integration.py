import unittest
from unittest.mock import MagicMock, patch
from src.agents.story_finder.agent import StoryFinderAgent
from src.agents.story_finder.models import StoryList, StoryIdea
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

class TestStoryFinderIntegration(unittest.TestCase):
    
    def setUp(self):
        # Setup mocks
        self.mock_llm_patcher = patch('src.agents.base_agent.ChatGoogleGenerativeAI')
        self.mock_tavily_patcher = patch('src.agents.story_finder.agent.TavilySearchResults')
        self.mock_settings_patcher = patch('src.agents.story_finder.agent.settings')
        
        self.mock_llm_class = self.mock_llm_patcher.start()
        self.mock_tavily_class = self.mock_tavily_patcher.start()
        self.mock_settings = self.mock_settings_patcher.start()
        
        # Configure settings
        self.mock_settings.USE_REAL_LLM = True
        self.mock_settings.GEMINI_API_KEY = "dummy_key"
        self.mock_settings.TAVILY_API_KEY = "dummy_tavily_key"
        self.mock_settings.llm_model_name = "gemini-pro"
        
        # Setup instances
        self.mock_llm_instance = MagicMock()
        self.mock_llm_class.return_value = RunnableLambda(self.mock_llm_instance)
        
        self.mock_search_tool_instance = MagicMock()
        self.mock_tavily_class.return_value = self.mock_search_tool_instance
        self.mock_search_tool_instance.invoke.return_value = "Mock Search Results"
        
        # Valid JSON response
        self.valid_json = """
        {
            "stories": [
                {
                    "title": "Integration Story",
                    "summary": "A story generated in integration test.",
                    "hook": "Integration Hook",
                    "keywords": ["integration", "test"],
                    "category": "news",
                    "mood": "exciting"
                }
            ]
        }
        """
        self.mock_llm_instance.return_value = AIMessage(content=self.valid_json)

    def tearDown(self):
        self.mock_llm_patcher.stop()
        self.mock_tavily_patcher.stop()
        self.mock_settings_patcher.stop()

    def test_find_stories_end_to_end(self):
        """Test find_stories method returns parsed StoryList."""
        agent = StoryFinderAgent()
        
        result = agent.find_stories(
            subject="Integration Test",
            num_stories=1,
            category="news",
            mood="exciting"
        )
        
        self.assertIsInstance(result, StoryList)
        self.assertEqual(len(result.stories), 1)
        self.assertEqual(result.stories[0].title, "Integration Story")
        self.assertEqual(result.stories[0].category, "news")
        
        # Verify search was called
        self.mock_search_tool_instance.invoke.assert_called()

if __name__ == '__main__':
    unittest.main()
