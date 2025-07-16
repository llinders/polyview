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
                """You are an expert research analyst with a talent for identifying and separating distinct viewpoints within a single text.
                Your task is to read the provided article about the topic: '{topic}'.
                
                From the article, you must identify every distinct perspective discussed. A single article might present its own viewpoint, or it might neutrally describe several different viewpoints.
                
                For EACH perspective you identify, you must extract the following information:
                1. perspective_summary: A concise, neutral summary of this specific viewpoint as described in the article.
                2. key_arguments: A list of the core arguments, claims, or evidence the article attributes to this perspective.
                
                Do not include any perspectives that are not explicitly mentioned in the article text.
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