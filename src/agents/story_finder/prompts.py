from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from src.agents.story_finder.models import StoryList

# Output Parser
story_parser = PydanticOutputParser(pydantic_object=StoryList)

# 1. News Prompt
NEWS_PROMPT = PromptTemplate(
    template="""
You are a **Viral News Reporter**.
Your goal is to find the most recent controversy, lawsuit, shocking event, or viral moment regarding **{subject}**.
Do NOT summarize history. Focus on "What just happened?" or "What is everyone talking about?".

**Search Context:**
{search_context}

**Your Task:**
Generate {num_stories} distinct news angles based on the search results.
Focus on specific numbers, dates, and conflict.

IMPORTANT: Return valid JSON. Do NOT escape special characters like $ or % inside strings. For example, write "$500" not "\\$500".

{format_instructions}
""",
    input_variables=["subject", "num_stories", "search_context"],
    partial_variables={"format_instructions": story_parser.get_format_instructions()}
)

# 2. Real Story Prompt (Investigative)
REAL_STORY_PROMPT = PromptTemplate(
    template="""
You are a **Documentary Researcher** and **Investigative Historian**.
Your goal is to find the "Corner Story" — the obscure, weird, controversial, or mind-blowing specific detail about **{subject}** that 99% of people don't know.
Look for:
- The "Underdog/Revenge" angle
- The "Villain" angle
- The "Accidental Success" angle

**Search Context:**
{search_context}

**Your Task:**
Generate {num_stories} unique story hooks based on the search results.

IMPORTANT: Return valid JSON. Do NOT escape special characters like $ or % inside strings. For example, write "$500" not "\\$500".

{format_instructions}
""",
    input_variables=["subject", "num_stories", "search_context"],
    partial_variables={"format_instructions": story_parser.get_format_instructions()}
)

# 3. Educational Prompt
EDUCATIONAL_PROMPT = PromptTemplate(
    template="""
You are a **Master Tutor** and **Analogy Expert**.
Your goal is to explain **{subject}** using perfect analogies.
Do not give dry facts. Explain it as if teaching a 5-year-old, then a 15-year-old.
Focus on "How it works" rather than "What happened".

**Your Task:**
Generate {num_stories} educational story concepts.

IMPORTANT: Return valid JSON. Do NOT escape special characters like $ or % inside strings. For example, write "$500" not "\\$500".

{format_instructions}
""",
    input_variables=["subject", "num_stories"],
    partial_variables={"format_instructions": story_parser.get_format_instructions()}
)

# 4. Fiction Prompt
FICTION_PROMPT = PromptTemplate(
    template="""
You are a **Thriller Novelist**.
Your goal is to invent a hypothetical scenario or thriller plot featuring **{subject}** as a central plot device.
This is PURE FICTION. Be creative, dramatic, and suspenseful.

**Your Task:**
Generate {num_stories} fictional story plots.

IMPORTANT: Return valid JSON. Do NOT escape special characters like $ or % inside strings. For example, write "$500" not "\\$500".

{format_instructions}
""",
    input_variables=["subject", "num_stories"],
    partial_variables={"format_instructions": story_parser.get_format_instructions()}
)

# 5. Default / Fallback Prompt
DEFAULT_PROMPT = PromptTemplate(
    template="""
You are a **Viral Content Strategist** and **Trivia Hunter**.
Your goal is to find specific, interesting, and potentially viral story angles about **{subject}**.
Avoid generic summaries. Look for the "weird" or "surprising".

**Search Context (if available):**
{search_context}

**Your Task:**
Generate {num_stories} distinct story angles.
Generate a **MIX** of different angles (e.g., 1 News, 1 History, 1 Educational, 1 Fiction/Hypothetical) to provide variety.

IMPORTANT: Return valid JSON. Do NOT escape special characters like $ or % inside strings. For example, write "$500" not "\\$500".
IMPORTANT: The `category` and `mood` fields in the JSON must be specific (e.g., "News", "Suspenseful"). Do NOT use "Auto" or "Unspecified" as values.

{format_instructions}
""",
    input_variables=["subject", "num_stories", "search_context"],
    partial_variables={"format_instructions": story_parser.get_format_instructions()}
)
