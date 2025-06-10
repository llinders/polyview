from typing import List, Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    topic: str
    search_queries: List[str]
    raw_articles: List[dict]
    iteration: int