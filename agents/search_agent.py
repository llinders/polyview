from langchain_core.messages import HumanMessage
from langgraph.constants import END
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.types import Command
from langchain_google_genai import ChatGoogleGenerativeAI


llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)
tavily_tool = TavilySearchResults(max_results=5)

search_agent = create_react_agent(llm, tools=[tavily_tool])

def search_node(state: AgentState) -> Command:
    result = search_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="search")
            ]
        },
        goto=END
    )