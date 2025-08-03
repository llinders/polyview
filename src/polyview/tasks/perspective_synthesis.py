from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from polyview.core.llm_config import llm
from polyview.core.logging import get_logger
from polyview.core.state import FinalPerspective, State

logger = get_logger(__name__)


class FinalPerspectives(BaseModel):
    final_perspectives: list[FinalPerspective]


def perspective_synthesis_node(state: State) -> dict:
    """
    Synthesizes and de-duplicates arguments within each consolidated perspective for all perspectives at once.

    This node takes the clustered perspectives (from perspective_clustering_node) and uses an LLM
    to refine their arguments, merging similar or duplicate arguments into a single, concise statement
    for each perspective, in a single LLM call.
    """
    consolidated_perspectives = state.get("consolidated_perspectives")

    if not consolidated_perspectives:
        logger.info(
            "No consolidated perspectives found for synthesis. Skipping synthesis node.."
        )
        return {"final_perspectives": []}

    logger.info(
        f"--- Synthesizing arguments for {len(consolidated_perspectives)} consolidated perspectives in one go ---"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert synthesizer and analyst. Your task is to transform a list of aggregated perspectives into a final, detailed analysis.
For each perspective provided, you must perform the following steps:

1.  **Finalize the Narrative**: Review the `preliminary_synthesis` and the `aggregated_narratives`. Write a comprehensive and neutral final `narrative` that accurately captures the essence of the perspective.
2.  **Synthesize Core Arguments**: Analyze the `aggregated_arguments`. Merge any that are semantically similar or redundant into a single, clear, and concise statement. This will become the `core_arguments`.
3.  **Identify Common Assumptions**: Based on the narrative and arguments, identify the underlying `common_assumptions` of the perspective.
4.  **Determine Strengths and Weaknesses**: Analyze the `core_arguments` and `supporting_evidence`. Identify the `strengths` (e.g., well-supported by evidence, logically consistent) and `weaknesses` (e.g., relies on unstated assumptions, lacks evidence for key claims) of the perspective.

Your output must be a list of `FinalPerspective` objects, fully populated.
""",
            ),
            (
                "human",
                """Please synthesize the following aggregated perspectives into a final analysis:\n\n{perspectives_json}""",
            ),
        ]
    )

    structured_llm = llm.with_structured_output(FinalPerspectives)
    chain = prompt | structured_llm

    try:
        final_perspectives_obj: FinalPerspectives = chain.invoke(
            {"perspectives_json": consolidated_perspectives}
        )
        logger.info(
            f"Successfully synthesized arguments for {len(final_perspectives_obj.final_perspectives)} perspectives."
        )
        logger.debug(f"Final perspectives: {final_perspectives_obj}")

    except Exception as e:
        logger.error(
            f"Error synthesizing arguments for all perspectives: {e}\n"
            f"Using consolidated perspectives as backup"
        )
        return {"final_perspectives": []}

    return {"final_perspectives": final_perspectives_obj.final_perspectives}
