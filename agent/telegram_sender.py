import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

load_dotenv("config/.env")

async def send_briefing(message: str):
    """Send a message to your Telegram chat."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in config/.env")
        return

    bot = Bot(token=token)
    await bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="Markdown"
    )
    print("Briefing sent to Telegram!")

if __name__ == "__main__":
    asyncio.run(send_briefing("Hello from your Morning Briefing Agent! 🌅"))
