from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from database.LocalDB import deleteAllURLs, userLinksList
from keyboards.home import build_home

r = Router()

@r.callback_query(F.data == "deleteAllLinks")
async def call_deleteAllLinks(callback: CallbackQuery):
    checkIfHas = await userLinksList(callback.from_user.id)
    if not checkIfHas:
        await callback.message.edit_text(f"You have not any links to delete",
                                     reply_markup = None)
        builder = await build_home(callback.from_user.id)
        await callback.message.answer("Select action", reply_markup = builder.as_markup())
        return
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text = "Yes",
                                     callback_data = "deleteAllLinksYes"),
                InlineKeyboardButton(text = "Cancel",
                                     callback_data = "home"))
    await callback.message.edit_text(f"<b>Are you sure you want to delete all of your links?</b>",
                                     reply_markup = builder.as_markup(), parse_mode = ParseMode.HTML)
    
@r.callback_query(F.data == "deleteAllLinksYes")
async def call_DELETE_ALL_LINKS(callback: CallbackQuery):
    builder = await build_home(callback.from_user.id)
    await callback.message.edit_text(f"<b>You have submitted deleting all of your links</b>",
                                     reply_markup = None, parse_mode = ParseMode.HTML)
    resultBool, resultInt = await deleteAllURLs(callback.from_user.id)
    if resultBool:
        await callback.message.answer(f"<b>Successfully was deleted {resultInt} your links!</b>",
                                         parse_mode = ParseMode.HTML)
        await callback.message.answer("Select action", reply_markup = builder.as_markup())
    else:
        await callback.message.answer("Error occured while deleting links")
        await callback.message.answer("Select action", reply_markup = builder.as_markup())
