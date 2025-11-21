from langchain_google_genai import ChatGoogleGenerativeAI
from src.agents.script_writer.prompts import SCRIPT_WRITER_AGENT_TEMPLATE, VIDEO_SCRIPT_PARSER
from src.models.models import VideoScript
from src.core.config import settings

class ScriptWriterAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model_name,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7
        )
        self.chain = SCRIPT_WRITER_AGENT_TEMPLATE | self.llm | VIDEO_SCRIPT_PARSER

    def generate_script(self, subject: str, language: str = "English", max_video_scenes: int = 8) -> VideoScript:
        """Generate a video script for a given subject."""
        return self.chain.invoke({
            "subject": subject,
            "language": language,
            "max_video_scenes": max_video_scenes
        })
