from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart, Command, CommandObject, StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from keyboards.home import build_home
from database.NotionDB import addNotionRow
from typing import List
import re
from data.config import BOT_TOKEN

r = Router()

bot = Bot(BOT_TOKEN)

class NotionFromUser(StatesGroup):
    API = State()
    databaseID = State()

notionValues: list = [] # [0] - API, [1] - databaseID
previousMessage: int = 0

@r.callback_query(F.data == "addNotionLink")
async def call_addNotionLink(callback: CallbackQuery, state: FSMContext):
    global previousMessage
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text = "Back to home", 
                                     callback_data = "home"))
    
    await callback.message.edit_text('''We will need to get Notion API and Database ID
        Firtsly, send your Notion API''', reply_markup = builder.as_markup())
    await state.set_state(NotionFromUser.API)
    previousMessage = callback.message.message_id

@r.message(NotionFromUser.API)
async def state_getAPI(msg: Message, state: FSMContext):
    global previousMessage, notionValues
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text = "Back to home", 
                                     callback_data = "home"))
    await bot.edit_message_reply_markup(chat_id = msg.chat.id, 
                                        message_id = previousMessage,
                                        reply_markup = None)
    notionValues.append(msg.text)
    temp = await msg.answer("Great, now send your database ID", reply_markup = builder.as_markup())
    previousMessage = temp.message_id
    await state.set_state(NotionFromUser.databaseID)

@r.message(NotionFromUser.databaseID)
async def state_getDatabaseID(msg: Message, state: FSMContext):
    global notionValues, previousMessage
    await bot.edit_message_reply_markup(chat_id = msg.chat.id, message_id = previousMessage, reply_markup = None)
    #### if 'builder' was defined here before IF ELSE statement, new menu will have 'Add Notion link', because here notion have not added yet
    notionValues.append(msg.text)
    checkIfAdded = await addNotionRow(msg.from_user.id,
                                      notionAPI = notionValues[0],
                                      databaseID = notionValues[1])
    if checkIfAdded:
        builder = await build_home(msg.from_user.id)    
        await msg.answer('''Your Notion API and Database ID was successfully added
            <b>From now, all your adding URLs also will save into your Notion database</b>''',
            parse_mode = ParseMode.HTML)
        await msg.answer("Select action", reply_markup = builder.as_markup())
    else:
        builder = await build_home(msg.from_user.id)
        await msg.answer("Error occured while adding your values")
        await msg.answer("Select action", reply_markup = builder.as_markup())
    await state.clear()

    