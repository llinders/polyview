from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage

from agents.query_generation_agent import query_generation_agent
from core.state import State

if __name__ == "__main__":
    state: State = {
        "messages": [HumanMessage(content="Explain the current state of climate change debates.")],
        "topic": "Current state of climate change debate",
        "search_queries": [],
        "raw_articles": [],
        "iteration": 1
    }

    query_generation_agent(state)