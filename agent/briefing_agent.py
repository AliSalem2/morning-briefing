import os
import sys
import litellm
from dotenv import load_dotenv
from datetime import date


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv("config/.env")

from agent.model_config import get_model
from agent.telegram_sender import send_briefing

from servers.weather_mcp import get_weather
from servers.calendar_mcp import get_todays_events
from servers.news_mcp import get_top_news

import asyncio

async def run_briefing(model_name: str = None):
    print("Fetching your morning briefing...\n")

    model, api_base = get_model(model_name)
    print(f"Using model: {model}\n")

    weather, calendar, news = await asyncio.gather(
        get_weather("Berlin"),
        get_todays_events(),
        get_top_news("technology", "us")
    )

    news_lines = news.strip().splitlines()
    top_headlines = [l for l in news_lines if l.strip() and not l.startswith("Top")]
    top_headlines_text = "\n".join(top_headlines[:5]) if top_headlines else "No news available"
    context = f"""Write a morning briefing in exactly 3 sentences using ONLY this data. Do not add anything else.

Weather: {weather.splitlines()[1]}
Calendar: {calendar}
Top news: {top_headlines_text}"""

    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a concise assistant. Use only the data provided. Never invent information. Reply in 3 sentences."},
            {"role": "user", "content": context}
        ],
        "timeout": 300
    }
    if api_base:
        kwargs["api_base"] = api_base

    response = litellm.completion(**kwargs)

    print("=" * 50)
    print("YOUR MORNING BRIEFING")
    print("=" * 50)
    print(f"Weather : {weather.splitlines()[1]}")
    print(f"Calendar: {calendar}")
    print(f"News    :\n{top_headlines_text}")
    print("-" * 50)
    
    briefing_text = response.choices[0].message.content
    print(briefing_text)
    print("=" * 50)

    # Send to Telegram
    today = date.today().strftime("%A, %d %B %Y")
    telegram_message = (
        f"🌅 *Morning Briefing*\n"
        f"📅 {today}\n\n"
        f"🌤 *Weather*\n{weather.splitlines()[1]}\n\n"
        f"📆 *Calendar*\n"
        + "\n".join(f"• {line.strip('- ')}" for line in calendar.splitlines() if line.startswith("-"))
        + f"\n\n📰 *Top News*\n"
        + "\n".join(f"• {line.split('. ', 1)[1].split(' - ')[0]}" for line in top_headlines[:5] if '. ' in line)
        + f"\n\n💬 *Summary*\n{briefing_text}"
    )
    await send_briefing(telegram_message)

if __name__ == "__main__":
    # Change "haiku" to "sonnet", "local-small", or "local-mid" to switch models
    # Or leave empty to use whatever is set in config/.env

    asyncio.run(run_briefing()) # General with Claude 

    # asyncio.run(run_briefing("local-mid")) # Addded for local only

    # asyncio.run(run_briefing("local-small")) #  Addded for local TinyLlama


