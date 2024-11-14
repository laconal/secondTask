from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from database.LocalDB import addURL
from keyboards.home import build_home
from typing import List
import re

r = Router()

bot = Bot('7846532519:AAGzL7gmjSlgJyiikqQL177ujUtPDoFrhDs')

class MessageFromUser(StatesGroup):
    gettingText = State()

previousMessage = 0
URLsToSave: List = []
usedLinks: List = []

@r.callback_query(F.data == "sendLink")
async def call_sendLink(callback: CallbackQuery, state: FSMContext):
    global previousMessage
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text = "Back to home", 
                                     callback_data = "home"))
    await callback.message.edit_text(text = "Send your link", reply_markup = builder.as_markup())
    await state.set_state(MessageFromUser.gettingText)
    previousMessage = callback.message.message_id

@r.message(MessageFromUser.gettingText)
async def state_MessageFromUser(msg: Message, state: FSMContext):
    global previousMessage, URLsToSave
    await bot.edit_message_reply_markup(chat_id = msg.chat.id, message_id = previousMessage,
                                        reply_markup = None)
    builder = await build_home(msg.from_user.id)
    
    ### get message's source
    msgSource: str = " "
    if msg.forward_from_chat:
        if msg.forward_from_chat.type == "channel":
            if msg.forward_from_chat.username:
                msgSource = "t.me/"+msg.forward_from_chat.username
            else: msgSource = msg.forward_from_chat.id # provide channel ID
    elif msg.forward_from:
        if msg.forward_from.username:
            msgSource = "t.me/"+msg.forward_from.username
        else: msgSource = msg.forward_from.id # provide user's ID
    else:
        if msg.from_user.username:
            msgSource = "t.me/"+msg.from_user.username
        else: msgSource = msg.from_user.id
    ###

    ### fiding URLs in message ###
    foundURLs = []
    entities = msg.entities or []
    for item in entities:
        if item.type == "url":
            foundURLs.append(item.extract_from(msg.text))
    formattedResult = ''
    for text in foundURLs:
        formattedResult += text + '\n'
    ###

    if not foundURLs: # if there has not any elemnents
        await msg.answer("Your text does not contain any URL.")
        await msg.answer("Select action", reply_markup = builder.as_markup())
    elif len(foundURLs) == 1: # if there just one element)
        await msg.answer(f"Send URL is: <b>{foundURLs[0]}</b>", parse_mode=ParseMode.HTML)
        await msg.answer("Processing...")
        resultBool, resultText = await addURL(userID = msg.from_user.id, URL = foundURLs[0],
                              source = msgSource)
        if resultBool: await msg.answer(f"{resultText}")
        else: await msg.answer(f"{resultText}")
        await msg.answer("Select action", reply_markup = builder.as_markup())
    elif len(foundURLs) > 1: # if there more than one element
        builder = InlineKeyboardBuilder()
        URLsToSave = foundURLs.copy()
        for url in foundURLs:
            builder.add(InlineKeyboardButton(text = url, callback_data = f"selectSaveLinks_{url}_{msgSource}"))
        builder.adjust(2)
        builder.row(InlineKeyboardButton(text = "Save all links", callback_data = f"selectSaveLinks_All_{msgSource}"))
        builder.row(InlineKeyboardButton(text = "Cancel", callback_data = "home"))
        await msg.answer("Which one save?", reply_markup = builder.as_markup())
    await state.clear()

@r.callback_query(F.data.regexp(r"selectSaveLinks_"))
async def call_selectSaveLinks(callback: CallbackQuery):
    global usedLinks, URLsToSave
    callbackData = callback.data.split('_') # [1] - list of urls
                                            # [2] - message source
                                            # [3] - save all links OR total amount of links
    URL = callbackData[1]
    msgSource = callbackData[2]

    # check if need to save all URLs or not
    saveAll: bool = True if len(callbackData) == 3 and callbackData[1] == "All" else False
    if saveAll:
        await callback.message.answer("Selected all")
        await callback.message.edit_text("Processing...", reply_markup = None)
        builder = await build_home(callback.from_user.id)
        URLcounter = 0
        for text in URLsToSave:
            resultBool, resultText = await addURL(userID = callback.from_user.id, URL = text, source = msgSource)
            if resultBool: URLcounter += 1
        if URLcounter == len(URLsToSave):
            await callback.message.answer(f"{URLcounter} URLs was successfully added to database.")
        else:
            await callback.message.answer(f"{URLsToSave - URLcounter} URLs cannot be added to database, unknown error occured.")
        await callback.message.answer("Select action", reply_markup = builder.as_markup())
    else:
        await callback.message.edit_text("Processing...", reply_markup = None)

        if URL not in usedLinks:
            resultBool, resultText = await addURL(userID = callback.from_user.id, URL = URL, source = msgSource)
            if resultBool:
                await callback.message.answer(f"{resultText}")
                usedLinks.append(URL)
        URLsToSave.remove(URL)
        if not URLsToSave:
            builder = await build_home(callback.from_user.id)
            await callback.message.edit_text("There has no left links", reply_markup = None)
            await callback.message.answer("Select action", reply_markup = builder.as_markup())
            URLsToSave.clear()
            return
        builder = InlineKeyboardBuilder()
        for text in URLsToSave:
            builder.add(InlineKeyboardButton(text = text, 
                                             callback_data = f"selectSaveLinks_{text}_{msgSource}"))
        builder.adjust(2)
        builder.row(InlineKeyboardButton(text = "Save all links", callback_data = f"selectSaveLinks_All_{msgSource}"))
        builder.row(InlineKeyboardButton(text = "Cancel", callback_data = "home"))
        await callback.message.answer("Which one save too?", reply_markup = builder.as_markup())

