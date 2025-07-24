from typing import List

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from polyview.core.llm_config import llm
from polyview.core.logging import get_logger
from polyview.core.state import State, FinalPerspective

logger = get_logger(__name__)


class FinalPerspectives(BaseModel):
    final_perspectives: List[FinalPerspective]


# TODO: Ensure that the perspective synthesis node has all required information to complete final perspectives
#  (strengths, weaknesses, assumptions, general narrative; for each per perspective)
def perspective_synthesis_node(state: State) -> dict:
    """
    Synthesizes and de-duplicates arguments within each consolidated perspective for all perspectives at once.

    This node takes the clustered perspectives (from perspective_clustering_node) and uses an LLM
    to refine their arguments, merging similar or duplicate arguments into a single, concise statement
    for each perspective, in a single LLM call.
    """
    consolidated_perspectives = state.get("consolidated_perspectives")

    if not consolidated_perspectives:
        logger.info("No consolidated perspectives found for synthesis. Skipping synthesis node..")
        return {"final_perspectives": []}

    logger.info(
        f"--- Synthesizing arguments for {len(consolidated_perspectives)} consolidated perspectives in one go ---")

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert at synthesizing and de-duplicating arguments across multiple perspectives.
Your task is to review a list of perspectives, each with its own set of arguments. For each perspective, you must:
1.  **Synthesize Arguments**: Merge any arguments that are semantically similar or redundant into a single, clear, and concise statement.
2.  **Maintain Original Intent**: The synthesized arguments must accurately represent the original intent and meaning of the input arguments.

Example of argument synthesis (conceptual):
Input Argument List for a perspective:
  - "Nuclear power is a low-carbon energy source."
  - "Nuclear energy is a powerful low-carbon energy source."
  - "Produces large amounts of electricity without greenhouse gas emissions."
  - "The land use is relatively little"
  - "High energy density"
Output Synthesized Argument:
  - "Nuclear power is a low-carbon energy source with little greenhouse gas emissions."
  - "The land use is minimal"
  - "High energy density"

"""
            ),
            (
                "human",
                """Please synthesize arguments for the following perspectives:\n\n{perspectives_json}"""
            ),
        ]
    )

    structured_llm = llm.with_structured_output(FinalPerspectives)
    chain = prompt | structured_llm

    try:
        final_perspectives: FinalPerspectives = chain.invoke({"perspectives_json": consolidated_perspectives})
        logger.info(
            f"Successfully synthesized arguments for {len(final_perspectives.final_perspectives)} perspectives.")
        logger.debug(f"Final perspectives: {final_perspectives}")

    except Exception as e:
        logger.error(f"Error synthesizing arguments for all perspectives: {e}\n"
                     f"Using consolidated perspectives as backup")
        return {"final_perspectives": consolidated_perspectives}

    return {"final_perspectives": final_perspectives}
