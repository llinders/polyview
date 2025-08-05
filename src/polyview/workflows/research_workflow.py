from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph

from polyview.agents.search_agent import run_search_agent
from polyview.core.logging import get_logger
from polyview.core.state import State
from polyview.utils.helper import print_state_node
from polyview.workflows.perspective_analysis import graph as perspective_analysis_graph

logger = get_logger(__name__)

MAX_ITERATIONS = 2
MIN_ARTICLES_TO_SUMMARIZE = 3
MIN_PERSPECTIVES_TO_SUMMARIZE = 2


def research_supervisor_node(state: State) -> dict:
    """
    Manages the high-level research loop.

    Responsibilities:
    1.  On the first run, it initializes the state with the user's topic.
    2.  On subsequent runs, it increments the iteration counter to track progress.
    """
    iteration = state.get("iteration", 0)

    if iteration == 0:
        topic = state.get("topic", "")
        if not topic:
            raise ValueError("State has no set topic.")
        logger.info(f"Initializing with topic: '{topic}'")
        return {
            "topic": topic,
            "iteration": 1,
            "messages": [AIMessage(content=f"Starting research for '{topic}'.")],
        }

    iteration += 1
    logger.info(f"Beginning research cycle {iteration}.")
    return {
        "iteration": iteration,
        "messages": [AIMessage(content=f"Running research cycle {iteration}...")],
    }


def decide_what_to_do(state: State) -> Literal["search_agent", "debug_state"]:
    """
    Decision point for the graph.

    This function evaluates the current state to decide whether to continue
    gathering data ("query_generation") or to proceed with summarizing the findings.
    """
    iteration = state["iteration"]
    raw_articles = state.get("raw_articles", [])
    perspectives = state.get("final_perspectives", [])

    logger.info(
        f"Decision point: Iteration: {iteration}, "
        f"Articles: {len(raw_articles)} (need {MIN_ARTICLES_TO_SUMMARIZE}), "
        f"Perspectives: {len(perspectives)} (need {MIN_PERSPECTIVES_TO_SUMMARIZE})"
    )

    if iteration > MAX_ITERATIONS:
        logger.info("Decision: Max iterations reached. Continuing.")
        return "debug_state"

    if iteration > 1:
        has_enough_articles = len(raw_articles) >= MIN_ARTICLES_TO_SUMMARIZE
        has_enough_perspectives = len(perspectives) >= MIN_PERSPECTIVES_TO_SUMMARIZE

        if has_enough_articles and has_enough_perspectives:
            logger.info(
                "Decision: Sufficient articles and perspectives found. Continuing."
            )
            return "debug_state"

    logger.info("Decision: More data or perspectives needed. Continuing research.")
    return "search_agent"


workflow = StateGraph(State)
workflow.add_node("supervisor", research_supervisor_node)
workflow.add_node("search_agent", run_search_agent)
workflow.add_node("perspective_analysis", perspective_analysis_graph)
workflow.add_node("debug_state", print_state_node)


workflow.set_entry_point("supervisor")
workflow.add_conditional_edges(
    "supervisor",
    decide_what_to_do,
    {
        "search_agent": "search_agent",
        "debug_state": "debug_state",
    },
)
workflow.add_edge("search_agent", "perspective_analysis")
workflow.add_edge("perspective_analysis", "supervisor")
workflow.set_finish_point("debug_state")

graph = workflow.compile()
