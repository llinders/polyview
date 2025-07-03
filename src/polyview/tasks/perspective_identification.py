import json
from typing import List

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from polyview.core.llm_config import llm
from polyview.core.state import State


class Evidence(BaseModel):
    """A piece of evidence supporting a perspective, directly extracted or summarized from the articles."""
    statement: str = Field(description="A specific, verifiable statement or claim made in the articles that supports the perspective.")
    article_indices: List[int] = Field(description="List of indices for articles that contain this piece of evidence.")

class Perspective(BaseModel):
    """Represents a single, distinct perspective on the topic."""
    title: str = Field(description="A short, descriptive title for the perspective (e.g., 'Technological Optimists', 'Economic Realists').")
    summary: str = Field(description="A neutral, concise summary of the perspective's core argument and viewpoint.")
    evidence: List[Evidence] = Field(description="A list of key pieces of evidence that support this perspective.")

class MissingPerspective(BaseModel):
    """A potentially missing perspective that is important for a balanced view."""
    name: str = Field(description="The name of the missing perspective (e.g., 'Regulatory Hurdles', 'Social Impact').")
    justification: str = Field(description="A brief explanation of why this perspective is important to include for a comprehensive analysis.")

class PerspectiveAnalysis(BaseModel):
    """The complete analysis of perspectives on a given topic, based on a set of articles."""
    overall_summary: str = Field(description="A high-level summary of the topic, acknowledging the main areas of agreement and disagreement.")
    perspectives: List[Perspective] = Field(description="A list of the distinct perspectives identified in the articles.")
    missing_perspectives: List[MissingPerspective] = Field(description="A list of important perspectives that were not found in the articles but are crucial for a balanced view.")


PERSPECTIVE_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a senior research analyst with expertise in synthesizing complex information from multiple sources. Your task is to analyze a collection of articles on a specific topic and produce a comprehensive, structured analysis of the different perspectives presented.

**Instructions:**

1.  **Overall Summary:** First, provide a high-level summary of the topic itself. This should briefly introduce the subject and touch upon the main points of contention or discussion found in the articles.

2.  **Identify Distinct Perspectives:**
    *   Do not just summarize each article. Synthesize the information to identify underlying *viewpoints* or *schools of thought*. A perspective is a way of interpreting the issue, not just a topic.
    *   For each distinct perspective you identify, you must:
        a.  Create a clear, descriptive **title**.
        b.  Write a neutral **summary** of its core arguments.
        c.  Extract key **evidence**. Each piece of evidence should be a concrete statement from the articles. For each statement, list the indices of the articles that support it.

3.  **Identify Missing Perspectives:**
    *   Analyze the collected perspectives. Are there any obvious gaps?
    *   List any crucial perspectives that are missing and explain why they are important for a balanced understanding.

4.  **Output Format:**
    *   Structure your entire output as a single JSON object conforming to the `PerspectiveAnalysis` schema.
    *   Ensure that article indices are correctly assigned and that no article is left out unless it is completely irrelevant. An article can support multiple pieces of evidence across different perspectives.
""",
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


def perspective_identification_node(state: State) -> dict:
    """
    Analyzes scraped articles to synthesize distinct perspectives, extract evidence, and identify knowledge gaps.
    """
    print("--- Running Perspective Analysis ---")
    topic = state["topic"]
    raw_articles = state["raw_articles"]

    formatted_articles = json.dumps(
        {i: article['content'][:4000] for i, article in enumerate(raw_articles)}, indent=2
    )

    structured_llm = llm.with_structured_output(PerspectiveAnalysis)
    chain = PERSPECTIVE_ANALYSIS_PROMPT | structured_llm

    print("Synthesizing perspectives from articles...")
    analysis_result = chain.invoke({"topic": topic, "articles": formatted_articles})

    print("\n--- Analysis Complete ---")
    print(f"Overall Summary: {analysis_result.overall_summary}")

    if analysis_result.perspectives:
        print(f"\nIdentified {len(analysis_result.perspectives)} perspectives:")
        for p in analysis_result.perspectives:
            print(f"  - Perspective: {p.title}")
            print(f"    Summary: {p.summary}")
            for ev in p.evidence:
                print(f"      - {ev.statement} (from articles {ev.article_indices})")
    else:
        print("\nWarning: No distinct perspectives were synthesized from the articles.")

    if analysis_result.missing_perspectives:
        print(f"\nIdentified {len(analysis_result.missing_perspectives)} potential knowledge gaps:")
        for gap in analysis_result.missing_perspectives:
            print(f"  - Missing: {gap.name} (Justification: {gap.justification})")
    else:
        print("\nNo obvious knowledge gaps were identified.")

    return {
        "identified_perspectives": [p.dict() for p in analysis_result.perspectives],
        "missing_perspectives": [p.dict() for p in analysis_result.missing_perspectives],
    }
