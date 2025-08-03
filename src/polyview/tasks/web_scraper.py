from langchain_community.document_loaders import WebBaseLoader
from langchain_core.tools import tool


@tool
def scrape_webpages(urls: list[str]) -> dict[str, str]:
    """
    Scrape the webpages from the given urls.

    :param urls: List of urls to scrape.
    :return: A dictionary where keys are the URLs and values are the content of the webpages.
    """
    loader = WebBaseLoader(
        web_paths=urls,
        continue_on_failure=True,
    )
    docs = loader.load()

    scraped_content = {}
    for doc in docs:
        url = doc.metadata.get("source")
        if url:
            scraped_content[url] = doc.page_content

    return scraped_content
