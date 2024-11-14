from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.LocalDB import userLinksList, getRowsBy
from typing import List

r = Router()

@r.callback_query(F.data.regexp(r"getLinks_"))
async def call_getLinks(callback: CallbackQuery):
    byWhat = callback.data.split('_')[1]
    builder = InlineKeyboardBuilder()
    links: List = await userLinksList(callback.from_user.id)
    if byWhat == "allLinks":
        for text in links:
            builder.add(InlineKeyboardButton(text = text["Title"] or text["URL"],
                                                callback_data = f"userLink_{text['ID']}_{text['URL']}"))
        builder.add(InlineKeyboardButton(text = "Back to home",
                                         callback_data = "home"))
        builder.adjust(2)
        await callback.message.edit_text("Your URL(s)", reply_markup = builder.as_markup())
        previousMessage = callback.message.message_id
    elif byWhat == "byCategory":
        usedValues = []
        for text in links:
            if text["Category"] not in usedValues:
                builder.add(InlineKeyboardButton(text = text["Category"] if text["Category"] else "Not specified",
                                                callback_data = f"userLink_by_Category_{text['Category']}"))
                usedValues.append(text["Category"])
        builder.add(InlineKeyboardButton(text = "Back to home", callback_data = "home"))
        builder.adjust(2)
        await callback.message.edit_text("Select category", reply_markup = builder.as_markup())
        previousMessage = callback.message.message_id
    elif byWhat == "bySource":
        usedValues = []
        for text in links:
            if text["Source"] not in usedValues:
                builder.add(InlineKeyboardButton(text = text["Source"] if text["Source"] else "Not specified",
                                                callback_data = f"userLink_by_Source_{text['Source']}"))
                usedValues.append(text["Source"])
        builder.add(InlineKeyboardButton(text = "Back to home", callback_data = "home"))
        builder.adjust(2)
        await callback.message.edit_text("Select source", reply_markup = builder.as_markup())
        previousMessage = callback.message.message_id
    elif byWhat == "byPriority":
        usedValues = []
        for text in links:
            if text["Priority"] not in usedValues:
                builder.add(InlineKeyboardButton(text = str(text["Priority"]) if text["Priority"] else "Not specified",
                                                callback_data = f"userLink_by_Priority_{text['Priority']}"))
                usedValues.append(text["Priority"])
        builder.add(InlineKeyboardButton(text = "Back to home", callback_data = "home"))
        builder.adjust(2)
        await callback.message.edit_text("Select priority", reply_markup = builder.as_markup())
        previousMessage = callback.message.message_id

@r.callback_query(F.data.regexp(r"userLink_by_"))
async def call_userLinkByProperty(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    property = callback.data.split('_')[2]
    propertyValue = callback.data.split('_')[3]
    if propertyValue.isdigit(): propertyValue = int(propertyValue)
    elif propertyValue == "None": propertyValue = None
    links = await getRowsBy(callback.from_user.id, property, propertyValue)
    for text in links:
        builder.add(InlineKeyboardButton(text = text["Title"] if text["Title"] else text["URL"],
                                         callback_data = f"userLink_{text['ID']}_{text['URL']}"))
    builder.add(InlineKeyboardButton(text = "Back to home", callback_data = "home"))
    builder.adjust(2)
    await callback.message.edit_text("Select element", reply_markup = builder.as_markup())