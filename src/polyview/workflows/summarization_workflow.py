from langgraph.graph import StateGraph

from polyview.core.state import State
from polyview.tasks.summarize import summarize_node

workflow = StateGraph(State)

workflow.add_node("summarize", summarize_node)

workflow.set_entry_point("summarize")
workflow.set_finish_point("summarize")

summarization_workflow = workflow.compile()
