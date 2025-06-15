from typing import List, Literal

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_tavily import TavilySearch
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from src.core.llm_config import llm
from src.core.state import State


class Article(BaseModel):
    """Represents a single article found during the search."""
    url: str = Field(description="The URL of the article.")
    title: str = Field(description="The title of the article.")
    content: str = Field(description="A summary or relevant snippet of the article's content.")

class SearchAnalysis(BaseModel):
    """The final, structured output of the search process."""
    summary: str = Field(description="A brief summary of the overall findings from the search.")
    articles: List[Article] = Field(description="A list of unique, relevant articles found.")

search_tool = TavilySearch(max_results=3)
llm_with_tools = llm.bind_tools([search_tool])

def agent_node(state: State):
    """The decision point of the agent. It decides whether to call a tool or finish."""
    result = llm_with_tools.invoke(state["messages"])
    return {"messages": [result]}

def tool_node(state: State):
    """Executes tool calls."""
    tool_calls = state["messages"][-1].tool_calls
    tool_messages = []
    for tool_call in tool_calls:
        result = search_tool.invoke(tool_call["args"])
        tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
    return {"messages": tool_messages}

def formatter_node(state: State):
    """Final node. Takes the agent's summary and formats it into structured JSON."""
    formatter_llm = llm.with_structured_output(SearchAnalysis)
    formatter_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert at parsing and structuring information. Take the user's text, which is a summary of web research, and format it into the required JSON structure."),
        ("user", "{text_to_format}")
    ])
    formatting_chain = formatter_prompt | formatter_llm

    unstructured_output = state["messages"][-1].content
    structured_result = formatting_chain.invoke({"text_to_format": unstructured_output})

    unique_articles = {article.url: article for article in structured_result.articles}
    final_articles_as_dicts = [article.dict() for article in unique_articles.values()]
    
    # We also pass the final summary message to the state if needed elsewhere.
    final_summary_message = HumanMessage(content=f"Search summary: {structured_result.summary}")

    return {"raw_articles": final_articles_as_dicts, "messages": [final_summary_message]}

def should_continue(state: State) -> Literal["continue", "end"]:
    """Router that decides where to go next."""
    if state["messages"][-1].tool_calls:
        return "continue"
    return "end"

search_workflow = StateGraph(State)
search_workflow.add_node("agent", agent_node)
search_workflow.add_node("tools", tool_node)
search_workflow.add_node("formatter", formatter_node)
search_workflow.set_entry_point("agent")
search_workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",
        "end": "formatter",
    },
)
search_workflow.add_edge("tools", "agent")
search_workflow.add_edge("formatter", END)

search_agent_graph = search_workflow.compile()

def run_search_agent(state: State) -> dict:
    """Main entry point of the sub-graph. This function will be called from the main graph."""
    print("--- Main Workflow: Invoking Search Sub-Graph ---")
    mission = (
        f"Your mission is to conduct a comprehensive search on the topic: '{state['topic']}'. "
        f"Your goal is to gather a diverse set of high-quality articles that represent different perspectives. "
        f"Analyze the results from your initial searches. If they are one-sided, formulate and execute new queries to find contrasting or missing viewpoints. "
        f"When you are finished, summarize your findings and list the articles you used."
    )
    
    search_input = {"messages": [HumanMessage(content=mission)]}
    result_state = search_agent_graph.invoke(search_input)

    return {
        "raw_articles": result_state["raw_articles"],
        "messages": result_state["messages"]
    }