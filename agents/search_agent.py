from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langgraph.constants import END
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command

from core.llm_config import llm
from core.state import State


search_tool = TavilySearch(max_results=5)

search_agent = create_react_agent(llm, tools=[search_tool])

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


def search_node_test():
    state = {
        "messages": [HumanMessage(content="Explain the current state of climate change debates.")],
        "search_queries": ["Test search query"],
    }
    result = search_agent.invoke(state)
    return result["messages"][-1].content
