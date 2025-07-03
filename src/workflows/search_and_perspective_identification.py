import json

from langgraph.constants import END
from langgraph.graph import StateGraph

from src.tasks.perspective_identification import perspective_identification_node
from src.agents.search_agent import run_search_agent
from src.core.state import State


def print_state_node(state: State):
    print("\n--- Debug State ---")
    printable_state = {k: v for k, v in state.items() if k != 'raw_articles'}
    printable_state['raw_articles_count'] = len(state.get('raw_articles', []))
    print(json.dumps(printable_state, indent=2, default=str))
    return state


workflow = StateGraph(State)

workflow.add_node("run_search_agent", run_search_agent)
workflow.add_node("perspective_identification", perspective_identification_node)

workflow.add_node("debug_print", print_state_node)

workflow.set_entry_point("run_search_agent")
workflow.add_edge("run_search_agent", "perspective_identification")

workflow.add_edge("perspective_identification", "debug_print")
workflow.add_edge("debug_print", END)

graph = workflow.compile()