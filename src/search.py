import asyncio
import requests
from bs4 import BeautifulSoup
from langchain.tools import tool
from crawl4ai import AsyncWebCrawler

@tool
async def web_search(query: str, limit: int = 3):
    """
    Search DuckDuckGo and return summaries of the top results.

    Args:
        query: Search query.
        limit: Max number of results.

    Returns:
        Markdown summary of results.
    """
    print(f"🔍 Searching DuckDuckGo (HTML) for: '{query}'")
    url = "https://html.duckduckgo.com/html/"
    params = {"q": query}
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        # Step 1: Perform DuckDuckGo search
        resp = await asyncio.to_thread(requests.post, url, data=params, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        for link in soup.select(".result__a")[:limit]:
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
async def get_url_content(url: str) -> str:
    """
    Fetch and return markdown content from a URL.

    Args:
        url: The URL to fetch.

    Returns:
        Markdown content.
    """
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        return result.markdown
