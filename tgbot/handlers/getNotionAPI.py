from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart, Command, CommandObject, StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from keyboards.home import build_home
from database.NotionDB import addUserToNotion
from data.config import botToken
from typing import List
import asyncio
import re

r = Router()

bot = Bot(botToken)

class NotionFromUser(StatesGroup):
    API = State()
    databaseID = State()

asyncioTask: asyncio.Task
notionValues: list = [] # [0] - API, [1] - databaseID
previousMessage: int = 0

async def waitMessage(chatID, userID, state: FSMContext, timeout: int) -> None:
    global previousMessage
    await asyncio.sleep(timeout)
    await state.clear()
    builder = await build_home(userID)
    await bot.edit_message_reply_markup(chat_id = chatID, message_id = previousMessage, reply_markup = None)
    await bot.send_message(chatID, f"Time ({timeout} seconds) to get from you message is expired. Try again.",
                           reply_markup = builder.as_markup())

@r.callback_query(F.data == "addNotionLink")
async def call_addNotionLink(callback: CallbackQuery, state: FSMContext):
    global previousMessage, asyncioTask
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text = "Back to home", 
                                     callback_data = "home"))
    await callback.message.edit_text('''We will need to get Notion API and Database ID
        Firtsly, send your Notion API''', reply_markup = builder.as_markup())
    previousMessage = callback.message.message_id
    await state.set_state(NotionFromUser.API)
    asyncioTask = asyncio.create_task(waitMessage(callback.message.chat.id, callback.from_user.id,
                                    state, 30))

@r.message(NotionFromUser.API)
async def state_getAPI(msg: Message, state: FSMContext):
    global previousMessage, notionValues, asyncioTask
    asyncioTask.cancel()
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
    asyncioTask = asyncio.create_task(waitMessage(msg.chat.id, msg.from_user.id,
                                                  state, 30))

@r.message(NotionFromUser.databaseID)
async def state_getDatabaseID(msg: Message, state: FSMContext):
    global notionValues, previousMessage, asyncioTask
    asyncioTask.cancel()
    await bot.edit_message_reply_markup(chat_id = msg.chat.id, message_id = previousMessage, reply_markup = None)
    #### if 'builder' was defined here before IF ELSE statement, new menu will have 'Add Notion link', because here notion have not added yet
    notionValues.append(msg.text)
    checkIfAdded = await addUserToNotion(msg.from_user.id,
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

    