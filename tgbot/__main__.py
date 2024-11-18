import asyncio
import logging

import betterlogging as bl
import orjson
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import handlers
import keyboards
from data.config import botToken

def setup_logging():
    log_level = logging.INFO
    bl.basic_colorized_config(level=log_level)
    logger = logging.getLogger(__name__)
    logger.info("Starting bot")

def setup_keybords(dp: Dispatcher) -> None:
    dp.include_router(keyboards.setup())

def setup_handlers(dp: Dispatcher) -> None:
    dp.include_router(handlers.setup())

async def setup_aiogram(dp: Dispatcher) -> None:
    setup_keybords(dp)
    setup_handlers(dp)

async def aiogram_on_startup_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    await setup_aiogram(dispatcher)

async def aiogram_on_shutdown_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    await bot.session.close()
    await dispatcher.storage.close()

async def main():
    setup_logging()
    session = AiohttpSession(
        json_loads=orjson.loads,
    )

    bot = Bot(
        token=botToken,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    storage = MemoryStorage()

    dp = Dispatcher(
        storage=storage,
    )

    dp.startup.register(aiogram_on_startup_polling)
    dp.shutdown.register(aiogram_on_shutdown_polling)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
