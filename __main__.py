import logging
import asyncio
from aiogram.types import Message
from aiogram import Router, Bot, Dispatcher
from handlers import (getLinkFromMessage, getUserLinks, 
                      userLinks, deleteAllLinks, userLinksChanging,
                      getNotionAPI)
from keyboards import home
from config import BOT_TOKEN

async def main():
    bot = Bot(token = BOT_TOKEN)
    dp = Dispatcher()
    dp.include_routers(getLinkFromMessage.r, home.r, userLinks.r, deleteAllLinks.r,
                       getUserLinks.r, userLinksChanging.r, getNotionAPI.r)
    logging.basicConfig(level = logging.INFO)


    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
