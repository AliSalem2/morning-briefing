import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import asyncio
import litellm
from datetime import datetime, date

load_dotenv("config/.env")

from agent.model_config import get_model
from servers.weather_mcp import get_weather
from servers.calendar_mcp import get_todays_events
from servers.news_mcp import get_top_news

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

# Simple conversation history per chat
conversation_history = []

def is_authorized(update: Update) -> bool:
    return update.effective_chat.id == ALLOWED_CHAT_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    await update.message.reply_text(
        "👋 Hey! I'm your Morning Briefing Assistant.\n\n"
        "Commands:\n"
        "/briefing — full morning briefing\n"
        "/weather — current weather in Berlin\n"
        "/calendar — today's events\n"
        "/news — top headlines\n"
        "/clear — clear conversation history\n\n"
        "Or just ask me anything! 💬"
    )

async def briefing_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    await update.message.reply_text("⏳ Fetching your briefing...")

    model, api_base = get_model()

    weather, calendar, news = await asyncio.gather(
        get_weather("Berlin"),
        get_todays_events(),
        get_top_news("technology", "us")
    )

    news_lines = news.strip().splitlines()
    top_headlines = [l for l in news_lines if l.strip() and not l.startswith("Top")]

    context_text = f"""Write a morning briefing in exactly 3 sentences using ONLY this data.
Weather: {weather.splitlines()[1]}
Calendar: {calendar}
Top news:
{chr(10).join(top_headlines[:5])}"""

    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a concise assistant. Use only the data provided. Reply in 3 sentences."},
            {"role": "user", "content": context_text}
        ],
        "timeout": 30
    }
    if api_base:
        kwargs["api_base"] = api_base

    response = litellm.completion(**kwargs)
    briefing_text = response.choices[0].message.content

    today = date.today().strftime("%A, %d %B %Y")
    message = (
        f"🌅 *Morning Briefing*\n"
        f"📅 {today}\n\n"
        f"🌤 *Weather*\n{weather.splitlines()[1]}\n\n"
        f"📆 *Calendar*\n"
        + "\n".join(f"• {line.strip('- ')}" for line in calendar.splitlines() if line.startswith("-"))
        + f"\n\n📰 *Top News*\n"
        + "\n".join(f"• {line.split('. ', 1)[1].split(' - ')[0]}" for line in top_headlines[:5] if '. ' in line)
        + f"\n\n💬 *Summary*\n{briefing_text}"
    )
    await update.message.reply_text(message, parse_mode="Markdown")

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    await update.message.reply_text("⏳ Checking weather...")
    weather = await get_weather("Berlin")
    await update.message.reply_text(f"🌤 *Weather in Berlin*\n{weather}", parse_mode="Markdown")

async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    calendar = await get_todays_events()
    await update.message.reply_text(f"📆 *Today's Calendar*\n{calendar}", parse_mode="Markdown")

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    news = await get_top_news("technology", "us")
    news_lines = news.strip().splitlines()
    top_headlines = [l for l in news_lines if l.strip() and not l.startswith("Top")]
    message = "📰 *Top News*\n\n" + "\n".join(f"• {line.split('. ', 1)[1].split(' - ')[0]}" for line in top_headlines[:5] if '. ' in line)
    await update.message.reply_text(message, parse_mode="Markdown")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    conversation_history.clear()
    await update.message.reply_text("🧹 Conversation history cleared.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    user_message = update.message.text
    await update.message.chat.send_action("typing")

    # Add to history
    conversation_history.append({"role": "user", "content": user_message})

    # Keep last 10 messages for context
    recent_history = conversation_history[-10:]

    model, api_base = get_model()

    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful personal assistant. Be concise and friendly. Today is " + datetime.now().strftime("%A, %d %B %Y %H:%M") + "."}
        ] + recent_history,
        "timeout": 30
    }
    if api_base:
        kwargs["api_base"] = api_base

    response = litellm.completion(**kwargs)
    reply = response.choices[0].message.content

    # Add reply to history
    conversation_history.append({"role": "assistant", "content": reply})

    await update.message.reply_text(reply)

def main():
    print("🤖 Starting Morning Briefing Bot...")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("briefing", briefing_command))
    app.add_handler(CommandHandler("weather", weather_command))
    app.add_handler(CommandHandler("calendar", calendar_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✅ Bot is running. Send /start on Telegram.")
    app.run_polling()

if __name__ == "__main__":
    main()
