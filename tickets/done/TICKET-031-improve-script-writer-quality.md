Here is a comprehensive and detailed technical ticket designed for an AI coding assistant (or a human developer). It uses standard engineering terminology and clearly outlines the architecture changes required for your LangChain backend.

-----

# Feature Request: Implement Dynamic Prompt Routing and Web Search for "Story Finder" Agent

**Priority:** High
**Component:** Backend / Story Finder Agent
**Tech Stack:** Python, LangChain, Tavily API (or Google Search API)

## 1\. Context & Problem Statement

Currently, the **Story Finder Agent** uses a static, "one-size-fits-all" prompt regardless of the user's selected category. This results in generic, Wikipedia-style summaries (e.g., "Capital One is a large bank...") rather than engaging, viral, or "corner" stories.

To fix this, we need to transform the agent into a context-aware system that:

1.  Actively searches the web for fresh/niche data when necessary.
2.  Changes its "Persona" and "Prompt Strategy" based on the user's selected `Category` (News, Real Story, Educational, Fiction).

## 2\. Technical Objectives

Implement a **Dynamic Router** using LangChain (either `RunnableBranch`, `RouterChain`, or functional routing logic) to select the correct execution path based on the input `category`.

### The Routing Logic

The system must handle the following inputs: `subject`, `category`, `mood`.

| Category Input | Agent Persona | Web Search Required? | Objective |
| :--- | :--- | :--- | :--- |
| **`NEWS`** | **The Tabloid Journalist** | **YES** | Find viral controversies, recent hacks, stock crashes, or weird PR moves from the last 1-12 months. |
| **`REAL_STORY`** | **The Investigative Historian** | **YES** | Find obscure origins, founder feuds, "butterfly effect" moments, or specific irony in the entity's history. |
| **`EDUCATIONAL`** | **The Analogy Master (Tutor)** | **OPTIONAL** (Default: No) | Explain complex mechanics using simple metaphors. Focus on "How it works" rather than "What happened." |
| **`FICTION`** | **The Thriller Novelist** | **NO** | Invent a hypothetical scenario or thriller plot featuring the subject as a central plot device. |
| **`DEFAULT/AUTO`** | **The Trivia Hunter** | **YES** | General interesting facts (fallback logic). |

## 3\. Implementation Details

### Step A: Integrate Search Tool

  * Install and configure a search tool (Recommended: `tavily-python` for optimized LLM results, or `langchain_google_community`).
  * Create a tool definition that allows the LLM to generate its own *optimized search queries* (e.g., input "Capital One" -\> converts to query "Capital One weird founder stories controversy").

### Step B: Define Prompt Templates

Create distinct `PromptTemplate` objects for each category.

**1. Template: `NEWS_PROMPT`**

> "You are a Viral News Reporter. Do not summarize history. Search for the most recent controversy, lawsuit, or shocking event regarding {subject}. Focus on specific numbers, dates, and conflict."

**2. Template: `REAL_STORY_PROMPT`**

> "You are a Documentary Researcher. Find the 'Corner Story'—the obscure detail no one knows. Look for 'The Underdog' angle, 'The Villain' angle, or 'The Accidental Success' angle regarding {subject}. Use the search tool to verify specific details."

**3. Template: `EDUCATIONAL_PROMPT`**

> "You are a Master Tutor. Your goal is to explain {subject} using a perfect analogy. Do not give dry facts. Explain it as if teaching a 5-year-old, then a 15-year-old."

### Step C: Implement the Router Chain

Refactor the current `Story Finder` chain. Instead of a linear chain, implement a routing mechanism.

**Suggested Pseudocode (LangChain Expression Language style):**

```python
# 1. Define Branching Logic
branch = RunnableBranch(
    (lambda x: x["category"] == "news", news_chain),
    (lambda x: x["category"] == "real_story", real_story_chain),
    (lambda x: x["category"] == "fiction", fiction_chain),
    default_chain
)

# 2. Build the Full Chain
story_finder_chain = (
    {
        "subject": itemgetter("subject"),
        "category": itemgetter("category"),
        "mood": itemgetter("mood")
    }
    | branch
)
```

## 4\. Acceptance Criteria

1.  **Search Activation:** When `category="news"` or `category="real_story"` is selected, the console logs must show a search API call being made (e.g., to Tavily).
2.  **Search Dormancy:** When `category="fiction"` is selected, NO search API call should be made.
3.  **Persona Consistency:**
      * Input: `Subject="Capital One"`, `Category="News"` -\> Output must mention a recent event, lawsuit, or specific financial figure.
      * Input: `Subject="Capital One"`, `Category="Fiction"` -\> Output must be a made-up story (e.g., "The bank heist that never happened").
4.  **Format:** The output must still adhere to the JSON structure required by the `Script Writer` agent (list of story ideas).

## 5\. Example Constraints for the AI Coder

  * Use `langchain_core` runnables (`RunnablePassthrough`, `RunnableBranch`) if possible.
  * Ensure environment variables for search APIs (e.g., `TAVILY_API_KEY`) are handled securely.
  * Keep the prompt templates modular (separate file) so they can be easily edited later.
---
## ✅ Implementation Complete

**Implemented by:** Antigravity
**Implementation Date:** 2025-11-24
**Branch:** feature/TICKET-031-improve-story-finder

### What Was Implemented
Verified and tested the dynamic routing and web search capabilities for the Story Finder Agent.
- Confirmed `NEWS` and `REAL_STORY` categories trigger web search.
- Confirmed `FICTION` category skips web search.
- **Fixed:** `EDUCATIONAL` category now skips web search by default (as per ticket requirements), whereas it was previously searching.
- Added comprehensive unit and integration tests.

### Files Modified
- `src/agents/story_finder/agent.py` - Updated `search_step` to skip search for "educational" category.

### Tests Added
**Unit Tests:**
- `tests/unit/test_story_finder_routing.py`
  - `test_news_category_triggers_search`
  - `test_fiction_category_skips_search`
  - `test_real_story_category_triggers_search`
  - `test_educational_category_search_behavior`

**Integration Tests:**
- `tests/integration/test_story_finder_integration.py`
  - `test_find_stories_end_to_end`

### Verification Performed
- [✓] All new tests pass
- [✓] Manual verification of routing logic via tests

### Deviations from Original Plan
- None significant.

### Additional Notes
- The ticket filename `TICKET-031-improve-script-writer-quality.md` is slightly misleading as the content is about "Story Finder Agent".
