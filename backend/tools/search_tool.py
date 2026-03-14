from duckduckgo_search import DDGS
from typing import Any


def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo — completely free, no API key needed.
    Returns formatted search results as a string.
    """
    try:
        results = []
        with DDGS() as ddgs:
            search_results = list(ddgs.text(query, max_results=max_results))

        if not search_results:
            return f"No results found for query: {query}"

        formatted = [f"Search results for: '{query}'\n"]
        for i, result in enumerate(search_results, 1):
            title = result.get("title", "No title")
            body = result.get("body", "No description")
            href = result.get("href", "No URL")
            formatted.append(f"{i}. {title}")
            formatted.append(f"   {body}")
            formatted.append(f"   Source: {href}")
            formatted.append("")

        return "\n".join(formatted)

    except Exception as e:
        return f"Search failed: {str(e)}. Try rephrasing the query."


def search_news(query: str, max_results: int = 5) -> str:
    """
    Search for recent news using DuckDuckGo.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=max_results))

        if not results:
            return f"No news found for: {query}"

        formatted = [f"News results for: '{query}'\n"]
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            body = result.get("body", "No description")
            source = result.get("source", "Unknown source")
            formatted.append(f"{i}. {title}")
            formatted.append(f"   {body}")
            formatted.append(f"   Source: {source}")
            formatted.append("")

        return "\n".join(formatted)

    except Exception as e:
        return f"News search failed: {str(e)}"


# LangChain compatible tool function
def run_search_tool(input: str) -> str:
    """
    Main entry point for the search tool.
    Input can be a plain query string.
    """
    return search_web(input)