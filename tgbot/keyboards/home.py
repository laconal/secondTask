from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart
from database.NotionDB import getNotionRow

r = Router()

async def build_home(userID: int = None) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text = "Send link",
                                    callback_data = "sendLink"),
                InlineKeyboardButton(text = "My links",
                                    callback_data = "myLinks"))
    
    # check if user has not added notion link yet
    checkUser = await getNotionRow(userID)
    if userID is not None and not checkUser[0]:
        builder.add(InlineKeyboardButton(text = "Add Notion link",
                                        callback_data = "addNotionLink"))
    builder.row(InlineKeyboardButton(text = "Delete all links",
                                    callback_data = "deleteAllLinks"))
    builder.adjust(2)
    return builder

@r.message(CommandStart())
async def cmdStart(msg: Message):
    builder = await build_home(msg.from_user.id)
    await msg.answer("Welcome to Notion Link Bot", reply_markup = builder.as_markup())

@r.callback_query(F.data == "home")
async def call_home(callback: CallbackQuery):
    builder = await build_home(callback.from_user.id)
    await callback.message.edit_text("Select action", reply_markup = builder.as_markup())