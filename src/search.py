import asyncio
import requests
from bs4 import BeautifulSoup
from langchain.tools import tool
from crawl4ai import AsyncWebCrawler

@tool
async def search_tool(query: str, number_of_search_results: int = 3):
    """
    Performs a DuckDuckGo search, fetches webpage content for each result,
    and returns summarized markdown snippets.

    Args:
        query: Search query string.
        number_of_search_results: Number of results to retrieve (default 3).

    Returns:
        A combined markdown text containing title, URL, and content snippet for each result.
    """
    print(f"🔍 Searching DuckDuckGo (HTML) for: '{query}'")
    url = "https://html.duckduckgo.com/html/"
    params = {"q": query}
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        # Step 1: Perform DuckDuckGo search
        resp = requests.post(url, data=params, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        for link in soup.select(".result__a")[:number_of_search_results]:
            title = link.get_text(strip=True)
            href = link.get("href")
            results.append({"title": title, "href": href})

        if not results:
            return "No results found."

        # Step 2: Fetch page content asynchronously
        async with AsyncWebCrawler() as crawler:
            tasks = [
                crawler.arun(url=r["href"])
                for r in results
                if r["href"].startswith("http")
            ]
            crawled = await asyncio.gather(*tasks, return_exceptions=True)

        # Step 3: Combine results
        output_lines = ["### 🔎 Search & Web Results\n"]
        for i, (r, page) in enumerate(zip(results, crawled)):
            output_lines.append(f"**Result {i+1}: {r['title']}**")
            output_lines.append(f"🔗 URL: {r['href']}")
            if isinstance(page, Exception):
                output_lines.append(f"⚠️ Error fetching content: {page}\n")
            else:
                text = page.markdown.strip()[:1000]  # limit to ~1000 chars
                output_lines.append(f"📄 Content Preview:\n{text}\n")

        return "\n".join(output_lines)

    except Exception as e:
        return f"Error performing search: {str(e)}"


@tool
async def url_content(url: str) -> str:
    """
    Fetches and returns the markdown content from a given URL.

    Args:
        url: The URL of the webpage to fetch content from.

    Returns:
        The markdown-formatted content of the webpage.
    """
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
        )
        return result.markdown
