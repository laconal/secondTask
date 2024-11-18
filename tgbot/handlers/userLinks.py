from aiogram import Router, F, Bot
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.enums import ParseMode
from database.LocalDB import userLinksList, getRowsBy, addRowToNotion, change
from database.NotionDB import getNotionRow
from keyboards.home import build_home
from typing import List
from data.config import botToken

r = Router()

bot = Bot(botToken)

class UserLinkAction(StatesGroup):
    changeURL = State()
    changeTitle = State()
    changeCategory = State()
    changePriority = State()

unsavedNotionURLs: List
userNotionValues: dict

@r.callback_query(F.data == "myLinks")
async def call_myLinks(callback: CallbackQuery):
    global unsavedNotionURLs, userNotionValues
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
        
        notionValues = await getNotionRow(callback.from_user.id)
        haveUnsavedURLs = await getRowsBy(callback.from_user.id, "inNotion", False)
        if notionValues[0] and haveUnsavedURLs:
            # getNotionRow()[0] - bool
            # if user have added his Notion API and have unsaved URLs from local to Notion database
            builder.add(InlineKeyboardButton(text = "Add all URLs to my Notion database",
                                                 callback_data = f"notion_saveAllLinks_{callback.from_user.id}"))
            unsavedNotionURLs = haveUnsavedURLs.copy()
            userNotionValues = notionValues[1].copy()
        builder.adjust(2)
        builder.row(InlineKeyboardButton(text = "Back to home", callback_data = "home"))
        await callback.message.edit_text("Select property", reply_markup = builder.as_markup())

@r.callback_query(F.data.regexp(r"notion_saveAllLinks_"))
async def call_notion_saveAllLinks(callback: CallbackQuery):
    global unsavedNotionURLs, userNotionValues
    await callback.message.edit_text("Processing...", reply_markup = None)
    builder = await build_home()
    counter = 0
    for i in unsavedNotionURLs:
        checkIfAdded = await addRowToNotion(i["ID"], i["userID"], i["URL"], i["Source"],
                                            userNotionValues["notionAPI"],
                                            userNotionValues["databaseID"])
        if checkIfAdded: 
            await change(i["ID"], "inNotion", True)
            counter += 1
    resultText: str
    if counter == len(unsavedNotionURLs):
        resultText = "All of your saved in your Notion database"
    else:
        resultText = f"Saved {counter} URLs in your Notion database, with others {len(unsavedNotionURLs - counter)} occured error while saving"
    await callback.message.answer(f"{resultText}")
    await callback.message.answer("Main menu", reply_markup = builder.as_markup())
    pass

