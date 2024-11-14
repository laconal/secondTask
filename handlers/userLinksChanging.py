from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart, Command, CommandObject, StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from database.LocalDB import userLinksList, removeURL, getRow, change
from keyboards.home import build_home
from .userLinks import previousMessage
from typing import List

r = Router()

bot = Bot('7846532519:AAGzL7gmjSlgJyiikqQL177ujUtPDoFrhDs')

class UserLinkAction(StatesGroup):
    changeURL = State()
    changeTitle = State()
    changeCategory = State()
    changePriority = State()

toChange: str = ''
rowData: dict = {}

@r.callback_query(F.data.regexp(r"userLink_(\d*)_"))
async def call_userLink(callback: CallbackQuery):
    global previousMessage, rowData
    URL = callback.data.split('_') # [1] - URL ID, [2] - URL
    rowInfo: dict = await getRow(int(URL[1]))
    if not rowInfo:
        await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = previousMessage,
                                            reply_markup = None)
        builder = await build_home(callback.from_user.id)
        await callback.message.answer("Error occured while getting URL information",
                                      reply_markup = builder.as_markup())
    else:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text = "Change URL", callback_data = f"userLinkAction_{URL[1]}_changeURL"),
                InlineKeyboardButton(text = "Change title", callback_data = f"userLinkAction_{URL[1]}_changeTitle"),
                InlineKeyboardButton(text = "Change category", callback_data = f"userLinkAction_{URL[1]}_changeCategory"),
                InlineKeyboardButton(text = "Change priority", callback_data = f"userLinkAction_{URL[1]}_changePriority"),
                InlineKeyboardButton(text = "Delete element", callback_data = f"userLinkAction_{URL[1]}_delete"),
                InlineKeyboardButton(text = "Back to home", callback_data = "home"))
        builder.adjust(2)
        await callback.message.edit_text(f'''Select action with URL <b>{rowInfo['Title']}</b>\n
        URL INFORMATION:
        URL: <b>{rowInfo['URL']}</b>
        Title: <b>{rowInfo['Title']}</b>
        Source: <b>{rowInfo['Source']}</b>
        Category: <b>{rowInfo['Category']}</b>
        Priority: <b>{rowInfo['Priority']}</b>
        Added time: <b>{rowInfo['timestamp']}</b>''', 
                                        reply_markup = builder.as_markup(), parse_mode = ParseMode.HTML)
        rowData = rowInfo.copy()
    
@r.callback_query(F.data.regexp(r"userLinkAction_(\d*)_"))
async def call_userLinkAction(callback: CallbackQuery, state: FSMContext):
    global previousMessage, rowData, toChange
    action = callback.data.split('_') # [1] - URL ID, [2] - action
    if action[2] == "delete":
        builder = await build_home(callback.from_user.id)
        result = await removeURL(action[1])
        if result:
            await callback.message.edit_text("URL has successfully removed!", reply_markup = builder.as_markup())
        else:
            await callback.message.edit_text("Error occured while deleting URL", reply_markup = builder.as_markup())
    elif action[2] in ["changeURL", "changeTitle", "changeCategory", "changePriority"]:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text = "Cancel", callback_data = "home"))
        if action[2] == "changeURL":
            await callback.message.edit_text(f"Send your new URL instead of {rowData['URL']}.", 
                                       reply_markup = builder.as_markup())
            previousMessage = callback.message.message_id
            await state.set_state(UserLinkAction.changeURL)
            toChange = "URL"
        elif action[2] == "changeTitle":
            await callback.message.edit_text(f"Send your new Title instead of {rowData['Title']}.", 
                                       reply_markup = builder.as_markup())
            previousMessage = callback.message.message_id
            await state.set_state(UserLinkAction.changeTitle)
            toChange = "Title"
        elif action[2] == "changeCategory":
            await callback.message.edit_text(f"Send your new Category instead of {rowData['Category']}.", 
                                       reply_markup = builder.as_markup())
            previousMessage = callback.message.message_id
            await state.set_state(UserLinkAction.changeCategory)
            toChange = "Category"
        elif action[2] == "changePriority":
            await callback.message.edit_text(f"Send your new Priority (number) instead of {rowData['Priority']}.", 
                                       reply_markup = builder.as_markup())
            previousMessage = callback.message.message_id
            await state.set_state(UserLinkAction.changePriority)
            toChange = "Priority"

@r.message(StateFilter(UserLinkAction.changeURL, UserLinkAction.changeTitle,
                       UserLinkAction.changeCategory, UserLinkAction.changePriority))
async def state_UserLinkAction_changeURL(msg: Message, state: FSMContext):
    global previousMessage, rowData, toChange

    await bot.edit_message_reply_markup(chat_id = msg.chat.id, message_id = previousMessage,
            reply_markup = None)
    builder = await build_home(msg.from_user.id)
    if toChange == "URL":
        entities = msg.entities or []
        URL = ''
        for item in entities:
            if item.type == "url":
                URL = item.extract_from(msg.text)
                break

        checkIfChanged = await change(urlID = rowData["ID"], property = "URL", value = URL)
        if checkIfChanged:
            await msg.answer(f"URL has been successfully changed to <b>{URL}</b>", parse_mode = ParseMode.HTML)
            await msg.answer("Select action", reply_markup = builder.as_markup())
            await state.clear()
        else: 
            await msg.answer("Error occured while changing URL")
            await msg.answer("Select action", reply_markup = builder.as_markup())
            await state.clear()
    elif toChange == "Title":
        checkIfChanged = await change(urlID = rowData["ID"], property = "Title", value = msg.text)
        if checkIfChanged:
            await msg.answer(f"Title has been successfully changed to <b>{msg.text}</b>", parse_mode = ParseMode.HTML)
            await msg.answer("Select action", reply_markup = builder.as_markup())
            await state.clear()
        else: 
            await msg.answer("Error occured while changing Title")
            await msg.answer("Select action", reply_markup = builder.as_markup())
            await state.clear()
    elif toChange == "Category":
        checkIfChanged = await change(urlID = rowData["ID"], property = "Category", value = msg.text)
        if checkIfChanged:
            await msg.answer(f"Category has been successfully changed to <b>{msg.text}</b>", parse_mode = ParseMode.HTML)
            await msg.answer("Select action", reply_markup = builder.as_markup())
            await state.clear()
        else: 
            await msg.answer("Error occured while changing Category")
            await msg.answer("Select action", reply_markup = builder.as_markup())
            await state.clear()
    elif toChange == "Priority":
        if not msg.text.isdigit():
            await msg.answer("As priority can be used only digits, not characters")
            await msg.answer("Select action", reply_markup = builder.as_markup())
            await state.clear()
        else:
            checkIfChanged = await change(urlID = rowData["ID"], property = "Priority", value = int(msg.text))
            if checkIfChanged:
                await msg.answer(f"Priority has been successfully changed to <b>{msg.text}</b>", parse_mode = ParseMode.HTML)
                await msg.answer("Select action", reply_markup = builder.as_markup())
                await state.clear()
            else: 
                await msg.answer("Error occured while changing Priority")
                await msg.answer("Select action", reply_markup = builder.as_markup())
                await state.clear()