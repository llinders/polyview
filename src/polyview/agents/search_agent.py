import hashlib
import json
from typing import Literal

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_tavily import TavilySearch
from langgraph.graph import END, StateGraph

from polyview.core.llm_config import llm
from polyview.core.logging import get_logger
from polyview.core.state import State

logger = get_logger(__name__)

# Constants for search agent search behavior
MIN_INITIAL_SEARCH_QUERIES = 2
MAX_INITIAL_SEARCH_QUERIES = 3
MAX_ADDITIONAL_QUERIES = 2

MAX_SEARCH_RESULTS_PER_QUERY = 3
MIN_MATCH_SCORE = 0.4  # Minimum matching score an article should have in correspondence to the query

search_tool = TavilySearch(max_results=MAX_SEARCH_RESULTS_PER_QUERY)
llm_with_tools = llm.bind_tools([search_tool])


def agent_node(state: State):
    """The decision point of the agent. It decides whether to call a tool or finish."""
    logger.debug(f"Messages in state of search agent subgraph: {state['messages']}")
    result = llm_with_tools.invoke(state["messages"])
    return {"messages": [result]}


def tool_node(state: State):
    """Executes tool calls and adds the result as ToolMessages to the state."""
    tool_calls = state["messages"][-1].tool_calls
    logger.debug(f"Executing tool calls: {tool_calls}")
    tool_messages = []
    for tool_call in tool_calls:
        result = search_tool.invoke(tool_call["args"])
        tool_messages.append(
            ToolMessage(content=json.dumps(result), tool_call_id=tool_call["id"])
        )
    return {"messages": tool_messages}


def process_results_node(state: State):
    """Processes search results and adds them to the state."""
    articles = []
    for message in state["messages"]:
        if isinstance(message, ToolMessage):
            content = json.loads(message.content)
            search_results = []
            if isinstance(content, dict):
                search_results = content.get("results", [])
            elif isinstance(content, list):
                search_results = content

            articles.extend(
                [
                    {**res, "id": hashlib.sha256(res["url"].encode()).hexdigest()}
                    for res in search_results
                    if res.get("score", 0) >= MIN_MATCH_SCORE
                ]
            )

    logger.info(f"Found {len(articles)} articles.")
    final_message = HumanMessage(content=f"Found {len(articles)} articles.")
    return {"raw_articles": articles, "messages": [final_message]}


def should_continue(state: State) -> Literal["continue", "end"]:
    """Router that decides where to go next."""
    if state["messages"][-1].tool_calls:
        return "continue"
    return "end"


search_workflow = StateGraph(State)
search_workflow.add_node("agent", agent_node)
search_workflow.add_node("tools", tool_node)
search_workflow.add_node("process_results", process_results_node)
search_workflow.set_entry_point("agent")
search_workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",
        "end": "process_results",
    },
)
search_workflow.add_edge("tools", "agent")
search_workflow.add_edge("process_results", END)

search_agent_graph = search_workflow.compile()


def run_search_agent(state: State) -> dict:
    """Main entry point for the search agent sub-graph."""
    logger.info("--- Invoking Search Sub-Graph ---")
    system_prompt = """You are a highly efficient search specialist. Your sole purpose is to find relevant articles for a given topic. Do not perform any analysis.

Your workflow is fast and iterative:
1.  **Initial Queries:** Start with about 3 broad search queries to quickly gather initial articles.
2.  **Refine if Necessary:** If the initial results seem one-sided, run 1-2 more targeted queries.
3.  **Conclude Quickly:** As soon as you have a diverse set of sources, conclude with 'END'."""

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "Please begin your research on the topic: '{topic}'"),
        ]
    )

    messages = prompt_template.format_messages(topic=state["topic"])
    search_input = {"messages": messages}
    result_state = search_agent_graph.invoke(search_input)

    return {
        "raw_articles": result_state.get("raw_articles", []),
        "messages": result_state.get("messages", []),
    }
