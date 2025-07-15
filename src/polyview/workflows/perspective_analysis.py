import json

from langgraph.graph import StateGraph

from polyview.agents.search_agent import run_search_agent
from polyview.core.state import State
from polyview.tasks.perspective_identification import perspective_identification


def print_state_node(state: State):
    print("\n--- Debug State ---")
    printable_state = {k: v for k, v in state.items() if k != 'raw_articles'}
    printable_state['raw_articles_count'] = len(state.get('raw_articles', []))
    print(json.dumps(printable_state, indent=2, default=str))
    return state

workflow = StateGraph(State)

## First run
# 1. Individual perspective identification
# 2. Perspective clustering & grouping arguments/facts (focus only on perspective and maybe a few arguments for more context and come up with a few core perspectives)
# 3. Perspective elaboration (synthesizing the core of all aggregated arguments)

## Other runs
# Instead of just creating a new perspective group from the new articles, we should check if they can be
# clustered into existing perspectives. If they can group them in there and review perspective elaboration if
# new arguments are presented. Otherwise: create a new perspective

workflow.add_node("search_agent", run_search_agent)
workflow.add_node("perspective_identification", perspective_identification)
workflow.add_node("debug_print", print_state_node)

workflow.set_entry_point("search_agent")
workflow.add_edge("search_agent", "perspective_identification")
workflow.add_edge("perspective_identification", "debug_print")
workflow.set_finish_point("debug_print")

graph = workflow.compile()