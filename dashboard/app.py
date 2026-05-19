import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import asyncio
import litellm
from datetime import datetime

load_dotenv("config/.env")

from agent.model_config import MODELS, get_model
from servers.weather_mcp import get_weather
from servers.calendar_mcp import get_todays_events
from servers.news_mcp import get_top_news
from agent.telegram_sender import send_briefing

app = FastAPI()
templates = Jinja2Templates(directory="dashboard/templates")

last_briefing = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    context = {
        "models": list(MODELS.keys()),
        "last_text": last_briefing.get("text"),
        "last_timestamp": last_briefing.get("timestamp"),
        "last_model": last_briefing.get("model"),
    }
    return templates.TemplateResponse(request=request, name="index.html", context=context)

@app.post("/run")
async def run_briefing_endpoint(request: Request):
    body = await request.json()
    model_name = body.get("model", None)
    send_to_telegram = body.get("telegram", False)

    model, api_base = get_model(model_name)

    weather, calendar, news = await asyncio.gather(
        get_weather("Berlin"),
        get_todays_events(),
        get_top_news("technology", "us")
    )

    news_lines = news.strip().splitlines()
    top_headlines = [l for l in news_lines if l.strip() and not l.startswith("Top")]

    context = f"""Write a morning briefing in exactly 3 sentences using ONLY this data.

Weather: {weather.splitlines()[1]}
Calendar: {calendar}
Top news:
{chr(10).join(top_headlines[:5])}"""

    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a concise assistant. Use only the data provided. Never invent information. Reply in 3 sentences."},
            {"role": "user", "content": context}
        ],
        "timeout": 30
    }
    if api_base:
        kwargs["api_base"] = api_base

    response = litellm.completion(**kwargs)
    briefing_text = response.choices[0].message.content

    last_briefing["text"] = briefing_text
    last_briefing["model"] = model
    last_briefing["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    last_briefing["weather"] = weather.splitlines()[1]
    last_briefing["calendar"] = calendar
    last_briefing["news"] = top_headlines[:5]

    if send_to_telegram:
        from datetime import date
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

    return {
        "briefing": briefing_text,
        "weather": last_briefing["weather"],
        "calendar": last_briefing["calendar"],
        "news": last_briefing["news"],
        "model": model,
        "timestamp": last_briefing["timestamp"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("dashboard.app:app", host="0.0.0.0", port=8000, reload=True)
