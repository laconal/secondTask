from aiogram import Router, F, Bot
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.enums import ParseMode
from database.LocalDB import userLinksList
from keyboards.home import build_home
from typing import List
from config import BOT_TOKEN

r = Router()

bot = Bot(BOT_TOKEN)

class UserLinkAction(StatesGroup):
    changeURL = State()
    changeTitle = State()
    changeCategory = State()
    changePriority = State()

previousMessage: int = 0

@r.callback_query(F.data == "myLinks")
async def call_myLinks(callback: CallbackQuery):
    global previousMessage
    links: List = await userLinksList(callback.from_user.id)
    if not links:
        builder = await build_home(callback.from_user.id)
        await callback.message.edit_text(f"<b>You have not added any URL(s) yet</b>", parse_mode = ParseMode.HTML,
                                         reply_markup = None)
        await callback.message.answer("Select action", reply_markup = builder.as_markup())
    else:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text = "By Category", 
                                        callback_data = "getLinks_byCategory"),
                    InlineKeyboardButton(text = "By Priority", 
                                        callback_data = "getLinks_byPriority"),
                    InlineKeyboardButton(text = "By Source", 
                                         callback_data = "getLinks_bySource"),
                    InlineKeyboardButton(text = "All links", 
                                        callback_data = "getLinks_allLinks"))
        builder.adjust(2)
        await callback.message.edit_text("Select property", reply_markup = builder.as_markup())
        previousMessage = callback.message.message_id

