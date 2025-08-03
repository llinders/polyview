from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from polyview.core.llm_config import llm
from polyview.core.logging import get_logger
from polyview.core.state import ArticlePerspectives, ExtractedPerspective, State

logger = get_logger(__name__)


class ExtractedPerspectives(BaseModel):
    perspectives: list[ExtractedPerspective] = Field(
        description="A list of extracted perspectives."
    )


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
                """You are an expert analyst skilled in identifying and deconstructing distinct viewpoints in a text.
Your task is to extract all clearly identifiable perspectives from the article regarding the topic of **{topic}**.

A perspective is a specific viewpoint, stance, or framing. 
For each one you find, you must populate the fields as provided in the 'ExtractedPerspectives' object.

Extract only what is explicitly presented or strongly implied in the text. Do not invent information. Keep each perspective distinct.
                """,
            ),
            (
                "human",
                "Analyze the following article text:\n\n---\n{article_text}\n---",
            ),
        ]
    )

    structured_llm = llm.with_structured_output(ExtractedPerspectives)
    chain = prompt | structured_llm

    articles_to_process = state.get("raw_articles")
    topic = state.get("topic")

    all_extracted_perspectives: list[ArticlePerspectives] = []

    logger.info(
        f"--- Identifying perspectives for {len(articles_to_process)} articles on topic: {topic} ---"
    )

    for article in articles_to_process:
        article_id = article["id"]
        logger.info(f"Processing article {article_id}: {article['url']}")
        try:
            extracted_object = chain.invoke(
                {"topic": topic, "article_text": article["content"]}
            )

            perspectives_list = extracted_object.perspectives

            if not isinstance(perspectives_list, list):
                logger.warning(
                    f"The 'perspectives' attribute is not a list. Response: {extracted_object}"
                )
                perspectives_list = []

            article_perspectives = ArticlePerspectives(
                source_article_id=article_id,
                perspectives=perspectives_list,
            )
            all_extracted_perspectives.append(article_perspectives)
            logger.info(f"Found {len(perspectives_list)} perspective(s).")

        except Exception as e:
            logger.error(f"Processing article {article_id} failed: {e}")

    return {"article_perspectives": all_extracted_perspectives}
