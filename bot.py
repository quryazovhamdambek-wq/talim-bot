import os
import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv

load_dotenv()

from database import init_db
from handlers import router
from branding import router as branding_router, setup_commands
from education import router as education_router

TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")
PORT = int(os.getenv("PORT", 8080))

if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set")

bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(router)
dp.include_router(branding_router)
dp.include_router(education_router)

async def on_startup(app):
    await init_db()
    await setup_commands(bot)
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/webhook/{TOKEN}"
        await bot.set_webhook(webhook_url)
        logging.info("Webhook o'rnatildi")

async def on_shutdown(app):
    await bot.delete_webhook(drop_pending_updates=False)
    await bot.session.close()

def main():
    logging.basicConfig(level=logging.INFO)
    if RENDER_URL:
        app = web.Application()
        app.on_startup.append(on_startup)
        app.on_shutdown.append(on_shutdown)
        handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        handler.register(app, path=f"/webhook/{TOKEN}")
        async def health_check(request):
            return web.Response(text="OK")
        app.router.add_get("/", health_check)
        setup_application(app, dp, bot=bot)
        web.run_app(app, host="0.0.0.0", port=PORT)
    else:
        async def run_polling():
            await init_db()
            await setup_commands(bot)
            logging.info("Bot polling rejimida ishga tushdi...")
            try:
                await dp.start_polling(bot)
            finally:
                await bot.session.close()
        asyncio.run(run_polling())

if __name__ == "__main__":
    main()
