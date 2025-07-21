from langgraph.graph import StateGraph

from polyview.core.state import State
from polyview.tasks.perspective_clustering import perspective_clustering_node
from polyview.tasks.perspective_identification import perspective_identification
from polyview.utils.helper import print_state_node

# Perspective analysis workflow, assuming articles are already present in state
workflow = StateGraph(State)

workflow.add_node("perspective_identification", perspective_identification)
workflow.add_node("perspective_clustering", perspective_clustering_node)
workflow.add_node("debug_print", print_state_node)

workflow.set_entry_point("perspective_identification")
workflow.add_edge("perspective_identification", "perspective_clustering")
workflow.add_edge("perspective_clustering", "debug_print")
workflow.set_finish_point("debug_print")

graph = workflow.compile()
