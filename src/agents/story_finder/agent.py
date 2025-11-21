import os
from langchain_google_genai import ChatGoogleGenerativeAI
from src.agents.story_finder.prompts import STORY_FINDER_TEMPLATE, story_parser
from src.agents.story_finder.models import StoryList
from src.core.config import settings

class StoryFinderAgent:
    def __init__(self):
        # Initialize LLM with proper configuration
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model_name,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7
        )
        self.chain = STORY_FINDER_TEMPLATE | self.llm | story_parser

    def find_stories(self, subject: str, num_stories: int = 5) -> StoryList:
        """Generate a list of story ideas for a given subject."""
        return self.chain.invoke({"subject": subject, "num_stories": num_stories})

