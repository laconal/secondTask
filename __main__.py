import logging
import asyncio
from aiogram.types import Message
from aiogram import Router, Bot, Dispatcher
from handlers import (getLinkFromMessage, getUserLinks, 
                      userLinks, deleteAllLinks, userLinksChanging,
                      getNotionAPI)
from keyboards import home

async def main():
    bot = Bot(token = '7846532519:AAGzL7gmjSlgJyiikqQL177ujUtPDoFrhDs')
    dp = Dispatcher()
    dp.include_routers(getLinkFromMessage.r, home.r, userLinks.r, deleteAllLinks.r,
                       getUserLinks.r, userLinksChanging.r, getNotionAPI.r)
    logging.basicConfig(level = logging.INFO)


    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
