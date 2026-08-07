import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv

load_dotenv()

from database import init_db
from handlers import router

TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(router)

async def on_startup(app):
    await init_db()
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/webhook/{TOKEN}"
        await bot.set_webhook(webhook_url)
        logging.info(f"Webhook o'rnatildi: {webhook_url}")

async def on_shutdown(app):
    if RENDER_URL:
        await bot.delete_webhook()

def main():
    logging.basicConfig(level=logging.INFO)
    
    if RENDER_URL:
        app = web.Application()
        app.on_startup.append(on_startup)
        app.on_shutdown.append(on_shutdown)

        handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        handler.register(app, path=f"/webhook/{TOKEN}")

        setup_application(app, dp, bot=bot)
        web.run_app(app, host="0.0.0.0", port=PORT)
    else:
        import asyncio
        async def run_polling():
            await init_db()
            print("Bot polling rejimida ishga tushdi...")
            await dp.start_polling(bot)
        asyncio.run(run_polling())

if __name__ == "__main__":
    main()
  
