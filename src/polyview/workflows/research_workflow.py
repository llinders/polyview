from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph

from polyview.agents.search_agent import run_search_agent
from polyview.core.state import State
from polyview.tasks.summarize import summarize_node

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
        messages = state.get("messages", [])
        if not messages:
            raise ValueError("State has no messages to extract a topic from.")
        topic = messages[-1].content
        print(f"Initializing with topic: '{topic}'")
        return {
            "topic": topic,
            "iteration": 1,
            "messages": [AIMessage(content=f"Starting research for '{topic}'.")]
        }

    iteration += 1
    print(f"\nBeginning research cycle {iteration}.")
    return {
        "iteration": iteration,
        "messages": [AIMessage(content=f"Running research cycle {iteration}...")]
    }


def decide_what_to_do(state: State) -> Literal["search_agent", "summarize"]:
    """
    Decision point for the graph.

    This function evaluates the current state to decide whether to continue
    gathering data ("query_generation") or to proceed with summarizing the findings.
    """
    iteration = state.get("iteration", 0)
    raw_articles = state.get("raw_articles", [])
    perspectives = state.get("identified_perspectives", [])

    print("--- Decision Analysis ---")
    print(f"Completed research cycles: {iteration}")
    print(f"Articles found: {len(raw_articles)} (need {MIN_ARTICLES_TO_SUMMARIZE})")
    print(f"Perspectives identified: {len(perspectives)} (need {MIN_PERSPECTIVES_TO_SUMMARIZE})")
    print("-------------------------")

    if iteration >= MAX_ITERATIONS:
        print("Decision: Max iterations reached. Proceeding to summary.")
        return "summarize"

    if iteration > 0:
        has_enough_articles = len(raw_articles) >= MIN_ARTICLES_TO_SUMMARIZE
        has_enough_perspectives = len(perspectives) >= MIN_PERSPECTIVES_TO_SUMMARIZE

        if has_enough_articles and has_enough_perspectives:
            print("Decision: Sufficient articles and perspectives found. Proceeding to summary.")
            return "summarize"

    print("Decision: More data or perspectives needed. Continuing research.")
    return "search_agent"


workflow = StateGraph(State)
workflow.add_node("supervisor", research_supervisor_node)
workflow.add_node("summarize", summarize_node)
workflow.add_node("search_agent", run_search_agent)
workflow.add_conditional_edges(
    "supervisor",
    decide_what_to_do
)
workflow.set_entry_point("supervisor")
workflow.set_finish_point("summarize")

graph = workflow.compile()