from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from polyview.core.logging import get_logger
from polyview.core.llm_config import llm
from polyview.core.state import State

logger = get_logger(__name__)


def query_generation_agent(state: State) -> dict:
    """
    Generates relevant search queries based on the topic and current iteration.
    Uses an LLM to generate diverse and targeted queries.
    """
    topic = state.get("topic")
    iteration = state.get("iteration", 1)

    logger.info(f"Query Generation Agent: Generating queries for '{topic}' (Iteration {iteration}).")

    if iteration == 1:
        # TODO: Refine prompt
        prompt_template = PromptTemplate.from_template(
            """You are a expert research assistant specialized in formulating search queries for a topic. 
            Based on the following topic, generate 3-5 diverse and effective search queries for a web search engine to gather comprehensive information.
            Focus on different angles, perspectives, and potential controversies related to the topic.
            Don't wrap queries in quotation marks, but it's fine to include quotes inside a query if needed.
            Provide each query on a new line (\\n).

            Topic: {topic}
            Queries:"""
        )
    else:
        # TODO: make more sophisticated by feeding identified_perspectives, fact_check_results (or unverified_claims). The goal is to target specific information gaps
        prompt_template = PromptTemplate.from_template(
            """You have already performed an initial search on '{topic}'.
            Based on the information gathered so far (implied by the iteration), generate 2-3 new, more specific or exploratory search queries to deepen the understanding or fact-check potential claims.
            Don't wrap queries in quotation marks, but it's fine to include quotes inside a query if needed.
            Provide each query on a new line (\\n).

            Topic: {topic}
            Queries:"""
        )

    query_chain = prompt_template | llm | StrOutputParser()

    try:
        response_text = query_chain.invoke({"topic": topic})
        logger.debug(f"Response text: {response_text!r}")
        # Split by newline character (\n) and clean whitespace
        queries = [q.strip() for q in response_text.split('\n') if q.strip()]
        if not queries:
            raise Exception(f"No queries generated from original response_text: {response_text}")
    except Exception as e:
        logger.error(f"Error generating queries with LLM: {e}. Falling back to default queries.")
        queries = [f"{topic} overview", f"{topic} key facts", f"{topic} all perspectives"]

    logger.info(f"Query Generation Agent: Generated queries: {queries}")
    return {"search_queries": queries}
