from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langchain_tavily import TavilySearch
from langgraph.constants import END
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command

from core.llm_config import llm
from core.state import State

search_agent_tool = TavilySearch(max_results=5)

search_agent = create_react_agent(llm, tools=[search_agent_tool])

def search_node(state: State) -> Command:
    result = search_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="search")
            ]
        },
        goto=END
    )

def run_search_queries(state: State) -> dict:
    """
    Runs the search queries found in the state and returns an update dictionary.
    """
    search_results_tool = TavilySearchResults(max_results=4)
    queries = state["search_queries"]
    print(f"Running {len(queries)} search queries...")
    all_results = []
    for query in queries:
        print(f"  - Searching for: '{query}'")
        results = search_results_tool.invoke(query)
        all_results.extend(results)

    print(f"Successfully retrieved {len(all_results)} articles from the web.")
    return {"raw_articles": all_results}
