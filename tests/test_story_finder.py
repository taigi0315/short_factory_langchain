import unittest
from unittest.mock import MagicMock, patch
from src.agents.story_finder.agent import StoryFinderAgent
from src.agents.story_finder.models import StoryList, StoryIdea

class TestStoryFinderAgent(unittest.TestCase):
    @patch('src.agents.story_finder.agent.ChatGoogleGenerativeAI')
    def test_find_stories(self, mock_llm_class):
        # Setup mock
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        
        # Mock the chain invocation
        # Since the chain is constructed in __init__, we need to mock the chain itself or the components
        # Easier to mock the invoke method of the chain if we can access it, 
        # or mock the components if we want to test the composition.
        # Given the implementation: self.chain = STORY_FINDER_TEMPLATE | self.llm | story_parser
        # It's a RunnableSequence.
        
        # Let's mock the invoke method of the agent's chain property if possible, 
        # or just mock the return value of the chain execution.
        
        agent = StoryFinderAgent()
        
        # Create a dummy response
        dummy_stories = StoryList(stories=[
            StoryIdea(title="Test Story", summary="Summary", hook="Hook", keywords=["test"])
        ])
        
        # Mock the chain's invoke method
        agent.chain = MagicMock()
        agent.chain.invoke.return_value = dummy_stories
        
        # Run method
        result = agent.find_stories("coffee", num_stories=1)
        
        # Verify
        self.assertEqual(len(result.stories), 1)
        self.assertEqual(result.stories[0].title, "Test Story")
        agent.chain.invoke.assert_called_once()

if __name__ == '__main__':
    unittest.main()
