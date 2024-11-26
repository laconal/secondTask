from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from database.LocalDB import userLinksList, removeURL, getRow, change
from database.NotionDB import getNotionRow, addRowToNotion
from keyboards.home import build_home
from data.config import botToken
import asyncio

r = Router()

bot = Bot(botToken)

class UserLinkAction(StatesGroup):
    changeURL = State()
    changeTitle = State()
    changeCategory = State()
    changePriority = State()

asyncioTask: asyncio.Task
toChange: str
rowData: dict
previousMessage: int
userNotionValues: dict

async def waitMessage(chatID, userID, state: FSMContext, timeout: int) -> None:
    global previousMessage
    await asyncio.sleep(timeout)
    await state.clear()
    builder = await build_home(userID)
    await bot.edit_message_reply_markup(chat_id = chatID, message_id = previousMessage, reply_markup = None)
    await bot.send_message(chatID, f"Time ({timeout} seconds) to get from you message is expired. Try again.",
                           reply_markup = builder.as_markup())

@r.callback_query(F.data.regexp(r"userLink_(\d*)_"))
async def call_userLink(callback: CallbackQuery):
    global previousMessage, rowData, userNotionValues
    URL = callback.data.split('_') # [1] - URL ID, [2] - URL
    rowInfo: dict | bool = await getRow(int(URL[1]))
    if not rowInfo:
        await callback.message.edit_reply_markup(reply_markup = None)
        builder = await build_home(callback.from_user.id)
        await callback.message.answer("Error occured while getting URL information",
                                      reply_markup = builder.as_markup())
    else:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text = "Change URL", callback_data = f"userLinkAction_{URL[1]}_changeURL"),
                InlineKeyboardButton(text = "Change title", callback_data = f"userLinkAction_{URL[1]}_changeTitle"),
                InlineKeyboardButton(text = "Change category", callback_data = f"userLinkAction_{URL[1]}_changeCategory"),
                InlineKeyboardButton(text = "Change priority", callback_data = f"userLinkAction_{URL[1]}_changePriority"),
                InlineKeyboardButton(text = "Delete element", callback_data = f"userLinkAction_{URL[1]}_delete"))
        
        checkIfUserHaveNotion = await getNotionRow(callback.from_user.id) # [0] - bool, [1] - row values (dict)
        if checkIfUserHaveNotion[0] and not rowInfo["inNotion"]: # check if URL has not added in Notion
            builder.add(InlineKeyboardButton(text = "Add to Notion", callback_data = f"userLinkAction_{URL[1]}_addToNotion"))
            userNotionValues = checkIfUserHaveNotion[1].copy()
        builder.row(InlineKeyboardButton(text = "Back to home", callback_data = "home"))
        builder.adjust(2)
        message = await callback.message.edit_text(f'''Select action with URL <b>{rowInfo['Title']}</b>\n
        URL INFORMATION:
        URL: <b>{rowInfo['URL']}</b>
        Title: <b>{rowInfo['Title']}</b>
        Source: <b>{rowInfo['Source']}</b>
        Category: <b>{rowInfo['Category']}</b>
        Priority: <b>{rowInfo['Priority']}</b>
        Added time: <b>{rowInfo['timestamp']}</b>''', 
                                        reply_markup = builder.as_markup(), parse_mode = ParseMode.HTML)
        rowData = rowInfo.copy()
        previousMessage = message.message_id
    
@r.callback_query(F.data.regexp(r"userLinkAction_(\d*)_"))
async def call_userLinkAction(callback: CallbackQuery, state: FSMContext):
    global previousMessage, rowData, toChange, userNotionValues, asyncioTask
    action = callback.data.split('_') # [1] - URL ID, [2] - action
    if action[2] == "delete":
        builder = await build_home(callback.from_user.id)
        result = await removeURL(action[1])
        if result:
            await callback.message.edit_text("URL has successfully removed!", reply_markup = builder.as_markup())
        else:
            await callback.message.edit_text("Error occured while deleting URL", reply_markup = builder.as_markup())
    elif action[2] in ["changeURL", "changeTitle", "changeCategory", "changePriority", "addToNotion"]:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text = "Cancel", callback_data = "home"))
        if action[2] == "changeURL":
            await callback.message.edit_text(f"Send your new URL instead of {rowData['URL']}.", 
                                       reply_markup = builder.as_markup())
            previousMessage = callback.message.message_id
            await state.set_state(UserLinkAction.changeURL)
            toChange = "URL"
            asyncioTask = asyncio.create_task(waitMessage(callback.message.chat.id, callback.from_user.id,
                                                          state, 10))
        elif action[2] == "changeTitle":
            await callback.message.edit_text(f"Send your new Title instead of {rowData['Title']}.", 
                                       reply_markup = builder.as_markup())
            previousMessage = callback.message.message_id
            await state.set_state(UserLinkAction.changeTitle)
            toChange = "Title"
            asyncioTask = asyncio.create_task(waitMessage(callback.message.chat.id, callback.from_user.id,
                                                          state, 10))
        elif action[2] == "changeCategory":
            await callback.message.edit_text(f"Send your new Category instead of {rowData['Category']}.", 
                                       reply_markup = builder.as_markup())
            previousMessage = callback.message.message_id
            await state.set_state(UserLinkAction.changeCategory)
            toChange = "Category"
            asyncioTask = asyncio.create_task(waitMessage(callback.message.chat.id, callback.from_user.id,
                                                          state, 10))
        elif action[2] == "changePriority":
            await callback.message.edit_text(f"Send your new Priority (number) instead of {rowData['Priority']}.", 
                                       reply_markup = builder.as_markup())
            previousMessage = callback.message.message_id
            await state.set_state(UserLinkAction.changePriority)
            toChange = "Priority"
            asyncioTask = asyncio.create_task(waitMessage(callback.message.chat.id, callback.from_user.id,
                                                          state, 10))
        elif action[2] == "addToNotion":
            builder = await build_home(callback.from_user.id)
            checkIfAdded = await addRowToNotion(rowData["ID"], rowData["userID"],
                                                rowData["URL"], rowData["Source"],
                                                userNotionValues["notionAPI"],
                                                userNotionValues["databaseID"])
            if checkIfAdded:
                await callback.message.edit_text(f"{rowData['Title']} successfully added to Notion database",
                                                 reply_markup = None)
                await change(rowData["ID"], "inNotion", True)
                await callback.message.answer("Select action", reply_markup = builder.as_markup())
            else:
                await callback.message.edit_text("Error occured while adding to Notion database")
                await callback.message.answer("Select action", reply_markup = builder.as_markup())

@r.message(StateFilter(UserLinkAction.changeURL, UserLinkAction.changeTitle,
                       UserLinkAction.changeCategory, UserLinkAction.changePriority))
async def state_UserLinkAction_changeURL(msg: Message, state: FSMContext):
    global previousMessage, rowData, toChange, asyncioTask
    asyncioTask.cancel()
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
        else: 
            await msg.answer("Error occured while changing URL")
            await msg.answer("Select action", reply_markup = builder.as_markup())
    elif toChange == "Title":
        checkIfChanged = await change(urlID = rowData["ID"], property = "Title", value = msg.text)
        if checkIfChanged:
            await msg.answer(f"Title has been successfully changed to <b>{msg.text}</b>", parse_mode = ParseMode.HTML)
            await msg.answer("Select action", reply_markup = builder.as_markup())
        else: 
            await msg.answer("Error occured while changing Title")
            await msg.answer("Select action", reply_markup = builder.as_markup())
    elif toChange == "Category":
        checkIfChanged = await change(urlID = rowData["ID"], property = "Category", value = msg.text)
        if checkIfChanged:
            await msg.answer(f"Category has been successfully changed to <b>{msg.text}</b>", parse_mode = ParseMode.HTML)
            await msg.answer("Select action", reply_markup = builder.as_markup())
        else: 
            await msg.answer("Error occured while changing Category")
            await msg.answer("Select action", reply_markup = builder.as_markup())
    elif toChange == "Priority":
        if not msg.text.isdigit():
            await msg.answer("As priority can be used only digits, not characters")
            await msg.answer("Select action", reply_markup = builder.as_markup())
        else:
            checkIfChanged = await change(urlID = rowData["ID"], property = "Priority", value = int(msg.text))
            if checkIfChanged:
                await msg.answer(f"Priority has been successfully changed to <b>{msg.text}</b>", parse_mode = ParseMode.HTML)
                await msg.answer("Select action", reply_markup = builder.as_markup())

            else: 
                await msg.answer("Error occured while changing Priority")
                await msg.answer("Select action", reply_markup = builder.as_markup())
