import json
from typing import List

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from core.llm_config import llm
from core.state import State


class IdentifiedPerspective(BaseModel):
    """A distinct perspective or viewpoint found in the articles."""
    name: str = Field(description="A short, descriptive name for the perspective (e.g., 'Pro-Technology Advocates', 'Economic Skeptics').")
    summary: str = Field(description="A neutral summary of this perspective's core argument.")
    article_indices: List[int] = Field(description="A list of indices corresponding to the articles that support this perspective.")

class MissingPerspective(BaseModel):
    """A potentially missing perspective that is important for a balanced view."""
    name: str = Field(description="The name of the missing perspective (e.g., 'Regulatory Hurdles', 'Social Impact').")
    justification: str = Field(description="A brief explanation of why this perspective is important to include for a comprehensive analysis.")

class ComprehensiveAnalysis(BaseModel):
    """The complete analysis, including identified and missing perspectives."""
    identified_perspectives: List[IdentifiedPerspective] = Field(description="A list of perspectives that were clearly identified in the provided articles.")
    missing_perspectives: List[MissingPerspective] = Field(description="A list of important perspectives that were not found in the articles but are crucial for a balanced view.")


COMPREHENSIVE_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an expert research analyst and critic. Your task is to analyze a collection of articles about a specific topic to identify the distinct perspectives within them and to find any crucial perspectives that are missing.

You will be given the research topic and a list of articles.

**Part 1: Identify Existing Perspectives**
1.  Read through all the articles and group them into clusters based on the underlying viewpoint or argument.
2.  For each perspective, provide a short, descriptive name and a summary of the core arguments and facts.
3.  List the indices of the articles that support each perspective. An article can only be assigned to one perspective.

**Part 2: Identify Missing Perspectives**
1.  After analyzing the existing articles, consider the overall topic.
2.  Identify any obvious, high-level perspectives that are missing but are crucial for a comprehensive and unbiased understanding.
3.  For each missing perspective, provide its name and a brief justification for why it's needed.

Structure your entire output as a single JSON object that conforms to the `ComprehensiveAnalysis` schema. If no significant perspectives are missing, return an empty list for `missing_perspectives`.""",
        ),
        (
            "user",
            """**Topic:** {topic}

**Articles:**
```json
{articles}
```""",
        ),
    ]
)


def perspective_identification_agent(state: State) -> dict:
    """
    Analyzes scraped articles to identify existing perspectives and find knowledge gaps in a single step.
    """
    print("--- Running Comprehensive Perspective Analysis ---")
    topic = state["topic"]
    raw_articles = state["raw_articles"]

    formatted_articles = json.dumps(
        {i: article['content'][:5000] for i, article in enumerate(raw_articles)}, indent=2
    )

    # --- Run Analysis ---
    structured_llm = llm.with_structured_output(ComprehensiveAnalysis)
    chain = COMPREHENSIVE_ANALYSIS_PROMPT | structured_llm
    
    print("Identifying existing perspectives and searching for knowledge gaps...")
    analysis_result = chain.invoke({"topic": topic, "articles": formatted_articles})

    # --- Process Results ---
    if analysis_result.identified_perspectives:
        print(f"Identified {len(analysis_result.identified_perspectives)} perspectives.")
    else:
        print("Warning: No perspectives were identified from the articles.")

    if analysis_result.missing_perspectives:
        print(f"Identified {len(analysis_result.missing_perspectives)} potential knowledge gaps.")
        for gap in analysis_result.missing_perspectives:
            print(f"  - Missing: {gap.name} (Justification: {gap.justification})")
    else:
        print("No obvious knowledge gaps were identified.")

    return {
        "identified_perspectives": analysis_result.identified_perspectives,
        "missing_perspectives": analysis_result.missing_perspectives,
    }