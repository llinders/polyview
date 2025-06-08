from typing import List

from langchain_core.tools import tool
from langgraph.prebuilt.chat_agent_executor import AgentState

@tool
def scrape_webpages(urls: List[str]) -> str:
    """
    Scrape the webpages from the given urls.

    :param urls: List of urls to scrape.
    :return: A string containing the scraped webpages.
    """
    #TODO: implement
    return "<Article name=Article 1>Content of article</Article> <Article name=Article 2>Article with different content</Article>"

def web_scraping_node(state: AgentState):
    """Scrapes internet using the provided search queries."""
    


