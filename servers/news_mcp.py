from fastmcp import FastMCP
import httpx
import os
from dotenv import load_dotenv

load_dotenv("config/.env")

mcp = FastMCP("news")

@mcp.tool()
async def get_top_news(category: str = "general", country: str = "de") -> str:
    """Get today's top news headlines. Category options: general, technology, science, business, health."""

    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return "NEWS_API_KEY not set in config/.env"

    url = (
        f"https://newsapi.org/v2/top-headlines"
        f"?category={category}&country={country}"
        f"&pageSize=5&apiKey={api_key}"
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()

    if data.get("status") != "ok":
        return f"News API error: {data.get('message', 'unknown error')}"

    articles = data.get("articles", [])
    if not articles:
        return "No headlines found."

    lines = [f"Top {category} headlines:\n"]
    for i, a in enumerate(articles, 1):
        title = a.get("title", "No title")
        source = a.get("source", {}).get("name", "Unknown")
        lines.append(f"{i}. {title} ({source})")

    return "\n".join(lines)

if __name__ == "__main__":
    mcp.run()
