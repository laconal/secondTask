from aiogram import Router
from aiogram.filters import CommandStart
# from keyboards.home import cmdStart
import keyboards

def setup() -> Router:
    router = Router()

    router.message.register(keyboards.home.cmdStart, CommandStart())
    router.include_routers(keyboards.home.r)

    return router
