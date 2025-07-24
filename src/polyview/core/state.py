from typing import List, Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field


class RawArticle(BaseModel):
    """Represents a single scraped article."""
    id: str
    url: str
    content: str


class ExtractedPerspective(BaseModel):
    """Represents a single perspective found within an article."""
    perspective_summary: str = Field(
        description="A concise summary of a distinct viewpoint expressed in the article.")
    key_arguments: List[str] = Field(
        description="A list of the main claims, rationales, or evidence supporting this perspective, as described in the article.")


class ArticlePerspectives(BaseModel):
    """A collection of extracted perspectives for a single article."""
    source_article_id: str
    perspectives: List[ExtractedPerspective]


class ConsolidatedPerspective(BaseModel):
    """
    Represents a final, clustered perspective with aggregated arguments of all articles.
    The summary serves as the name/identifier for this consolidated perspective.
    """
    perspective_name: str = Field(
        description="A short descriptive name for the perspective (e.g., 'Scientific Consensus', 'Techno-Optimist', "
                    "'Skeptical/Contrarian', 'Justice-Oriented', 'Economic Impact Concerns', 'Geopolitical Risks', "
                    "'Conservative', 'Liberal', etc.)")
    arguments: List[str]


class FinalPerspective(BaseModel):
    """
    The final, detailed analysis of a single perspective about the topic.
    This perspective is synthesized based on the aggregated arguments for the consolidated perspectives.
    """
    perspective_name: str = Field(
        description="A short descriptive name for the perspective (e.g., 'Scientific Consensus', 'Techno-Optimist', "
                    "'Skeptical/Contrarian', 'Justice-Oriented', 'Economic Impact Concerns', 'Geopolitical Risks', "
                    "'Conservative', 'Liberal', etc.)")
    narrative: str
    core_arguments: List[str]
    common_assumptions: List[str]
    strengths: List[str]
    weaknesses: List[str]


class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    topic: str

    raw_articles: List[RawArticle]
    article_perspectives: List[ArticlePerspectives]
    consolidated_perspectives: List[ConsolidatedPerspective]

    identified_perspectives: List[FinalPerspective]
    summary: str

    iteration: int
    missing_perspectives: List[dict]  # TODO: remove or change to List[str]
