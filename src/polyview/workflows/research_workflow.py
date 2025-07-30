from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph

from polyview.agents.search_agent import run_search_agent
from polyview.core.state import State
from polyview.tasks.perspective_identification import perspective_identification
from polyview.utils.helper import print_state_node

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


def decide_what_to_do(state: State) -> Literal["search_agent", "debug_state"]:
    """
    Decision point for the graph.

    This function evaluates the current state to decide whether to continue
    gathering data ("query_generation") or to proceed with summarizing the findings.
    """
    iteration = state["iteration"]
    raw_articles = state.get("raw_articles", [])
    perspectives = state.get("final_perspectives", [])

    print("--- Decision Analysis ---")
    print(f"Completed research cycles: {iteration}")
    print(f"Articles found: {len(raw_articles)} (need {MIN_ARTICLES_TO_SUMMARIZE})")
    print(f"Perspectives identified: {len(perspectives)} (need {MIN_PERSPECTIVES_TO_SUMMARIZE})")
    print("-------------------------")

    if iteration >= MAX_ITERATIONS:
        print("Decision: Max iterations reached. Continuing.")
        return "debug_state"

    if iteration > 1:
        has_enough_articles = len(raw_articles) >= MIN_ARTICLES_TO_SUMMARIZE
        has_enough_perspectives = len(perspectives) >= MIN_PERSPECTIVES_TO_SUMMARIZE

        if has_enough_articles and has_enough_perspectives:
            print("Decision: Sufficient articles and perspectives found. Continuing.")
            return "debug_state"

    print("Decision: More data or perspectives needed. Continuing research.")
    return "search_agent"


workflow = StateGraph(State)
workflow.add_node("supervisor", research_supervisor_node)
workflow.add_node("search_agent", run_search_agent)
workflow.add_node("debug_state", print_state_node)
workflow.add_node("perspective_identification", perspective_identification)
## First run
# 1. Individual perspective identification
# 2. Perspective clustering & grouping arguments/facts (focus only on perspective and maybe a few arguments for more context and come up with a few core perspectives)
# 3. Perspective elaboration (synthesizing the core of all aggregated arguments)

## Other runs
# Instead of just creating a new perspective group from the new articles, we should check if they can be
# clustered into existing perspectives. If they can group them in there and review perspective elaboration if
# new arguments are presented. Otherwise: create a new perspective
# TODO: add perspective clustering so that perspectives are grouped after individual identification
#  and add perspective elaboration, where all core arguments are summarized and a perspective is synthesized

# TODO: for runs where iteration>1 first identify perspectives for each article as before, but when clustering
#  check if they can be clustered into existing perspectives. After, check during
#  perspective elaboration if new arguments are present for resynthesis of the final perspective

workflow.set_entry_point("supervisor")
workflow.add_conditional_edges(
    "supervisor",
    decide_what_to_do
)
workflow.add_edge("search_agent", "perspective_identification")
workflow.add_edge("perspective_identification", "supervisor")
workflow.set_finish_point("debug_state")

graph = workflow.compile()
