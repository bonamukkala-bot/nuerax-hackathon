import wikipedia
from typing import Optional


def search_wikipedia(query: str, sentences: int = 5) -> str:
    """
    Search Wikipedia and return a summary of the topic.
    Completely free, no API key needed.
    """
    try:
        # Set language to English
        wikipedia.set_lang("en")

        # Search for the topic
        search_results = wikipedia.search(query, results=3)

        if not search_results:
            return f"No Wikipedia results found for: {query}"

        # Try to get the page
        try:
            page = wikipedia.page(search_results[0], auto_suggest=False)
            summary = wikipedia.summary(
                search_results[0],
                sentences=sentences,
                auto_suggest=False
            )

            result = f"Wikipedia: {page.title}\n\n"
            result += f"{summary}\n\n"
            result += f"Source: {page.url}"
            return result

        except wikipedia.DisambiguationError as e:
            # If disambiguation, try the first option
            try:
                page = wikipedia.page(e.options[0], auto_suggest=False)
                summary = wikipedia.summary(
                    e.options[0],
                    sentences=sentences,
                    auto_suggest=False
                )
                result = f"Wikipedia: {page.title}\n\n"
                result += f"{summary}\n\n"
                result += f"Source: {page.url}"
                return result
            except Exception:
                return f"Wikipedia found multiple matches for '{query}': {', '.join(e.options[:5])}"

        except wikipedia.PageError:
            # Try the second search result
            if len(search_results) > 1:
                try:
                    summary = wikipedia.summary(
                        search_results[1],
                        sentences=sentences,
                        auto_suggest=False
                    )
                    return f"Wikipedia: {search_results[1]}\n\n{summary}"
                except Exception:
                    pass
            return f"Wikipedia page not found for: {query}"

    except Exception as e:
        return f"Wikipedia search failed: {str(e)}"


def run_wikipedia_tool(input: str) -> str:
    """
    Main entry point for the Wikipedia tool.
    """
    input = input.strip()
    input = input.replace("wikipedia", "").strip()
    input = input.replace("search for", "").strip()
    input = input.replace("look up", "").strip()
    return search_wikipedia(input)