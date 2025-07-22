from typing import List

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from polyview.core.llm_config import llm
from polyview.core.state import State, ExtractedPerspective, ArticlePerspectives


class ExtractedPerspectives(BaseModel):
    perspectives: List[ExtractedPerspective] = Field(description="A list of extracted perspectives.")


def perspective_identification(state: State) -> dict:
    """
    Identifies and extracts one or more perspectives from each article.

    This node iterates through each raw article, invoking an LLM with structured output
    to extract all discussed perspectives.
    """
    # TODO: parallelize llm calls instead of looping

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert analyst skilled in identifying and clustering distinct viewpoints in a text.
Your task is to extract all clearly identifiable perspectives presented in the article about {topic}.

A perspective is any specific viewpoint, stance, or framing explicitly described or quoted in the article — whether from the author, sources, or referenced groups. Do not infer or invent perspectives; only use what is explicitly presented.

Example (for topic: universal basic income):
Perspective summary: UBI reduces poverty and empowers citizens.
Key arguments:
  * Provides a financial safety net regardless of employment.
  * Reduces bureaucracy compared to welfare systems.
  * Helps people focus on education, caregiving, or entrepreneurship.

Keep each perspective distinct, even if they overlap. Be neutral, concise, and only use what's in the text.
                """
            ),
            (
                "human",
                "Please analyze the following article text:\n\n---\n{article_text}\n---"
            ),
        ]
    )

    structured_llm = llm.with_structured_output(ExtractedPerspectives)
    chain = prompt | structured_llm

    articles_to_process = state.get("raw_articles")
    topic = state.get("topic")

    all_extracted_perspectives: List[ArticlePerspectives] = []

    print(f"--- Identifying perspectives for {len(articles_to_process)} articles on topic: {topic} ---")

    for article in articles_to_process:
        article_id = article["id"]
        print(f"Processing article {article_id}: {article["url"]}")
        try:
            extracted_object = chain.invoke({
                "topic": topic,
                "article_text": article["content"]
            })

            perspectives_list = extracted_object.perspectives

            if not isinstance(perspectives_list, list):
                print(f"  -> The 'perspectives' attribute is not a list... Response: {extracted_object}")
                perspectives_list = []

            article_perspectives = ArticlePerspectives(
                source_article_id=article_id,
                perspectives=perspectives_list,
            )
            all_extracted_perspectives.append(article_perspectives)
            print(f"  -> Found {len(perspectives_list)} perspective(s).")

        except Exception as e:
            print(f"  -> Error processing article {article_id}: {e}")

    return {"article_perspectives": all_extracted_perspectives}
