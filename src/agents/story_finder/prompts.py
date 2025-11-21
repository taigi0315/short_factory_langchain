from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from src.agents.story_finder.models import StoryList

# Parser
story_parser = PydanticOutputParser(pydantic_object=StoryList)

# Prompt
STORY_FINDER_PROMPT = """
You are a **Creative Researcher** and **Story Hunter**.
Your goal is to take a broad subject and find specific, interesting, and potentially viral story angles.
We are not looking for generic information. We want "The Coffee Poop Cat" type of stories - specific, weird, surprising, or deeply educational but with a twist.

## Input Subject
{subject}

## Your Task
Generate {num_stories} unique story ideas related to this subject.
Each story should be distinct and have a clear "hook".

## Criteria for Good Stories
1. **Specific**: Not "History of Coffee", but "How a goat herder discovered coffee".
2. **Surprising**: "Coffee was once banned by the Pope?"
3. **Visual Potential**: Can we show interesting images/animations?
4. **Emotional/Intellectual Engagement**: Makes the viewer say "Wow" or "I didn't know that".

{format_instructions}
"""

STORY_FINDER_TEMPLATE = PromptTemplate(
    template=STORY_FINDER_PROMPT,
    input_variables=["subject", "num_stories"],
    partial_variables={"format_instructions": story_parser.get_format_instructions()}
)
