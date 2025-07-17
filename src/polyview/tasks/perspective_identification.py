from langchain_core.prompts import ChatPromptTemplate

from polyview.core.llm_config import llm
from polyview.core.state import State, ArticlePerspectives


def perspective_identification(state: State) -> dict:
    """
    Identifies and extracts one or more perspectives from each article.

    This node iterates through each raw article, invoking an LLM with structured output
    to extract all discussed perspectives.
    """
    #TODO: parallelize llm calls instead of looping

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

    structured_llm = llm.with_structured_output(ArticlePerspectives)

    chain = prompt | structured_llm

    articles_to_process = state.get("raw_articles")
    topic = state.get("topic")
    
    perspectives_by_article = {}

    print(f"--- Identifying perspectives for {len(articles_to_process)} articles on topic: {topic} ---")

    for article in articles_to_process:
        print(f"Processing article {article['id']}: {article['url']}")
        try:
            response = chain.invoke({
                "topic": topic,
                "article_text": article["content"]
            })
            perspectives_by_article[article['id']] = response.perspectives
            print(f"  -> Found {len(response.perspectives)} perspective(s).")

        except Exception as e:
            print(f"  -> Error processing article {article['id']}: {e}")
            perspectives_by_article[article['id']] = []

    return {"extracted_perspectives": perspectives_by_article}