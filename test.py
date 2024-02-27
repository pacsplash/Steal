#!/usr/bin/python
# -*- coding: utf-8 -*-

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from aiogram.utils import executor

API_TOKEN = '6109082600:AAH-NEmSoeE8iE1-hlulEQXl5HVbPv1O5S0'

bot = Bot(token=API_TOKEN, parse_mode='html')

# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class CodeInput:
    data = {}


kb = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [
            types.InlineKeyboardButton(text='0️⃣', callback_data='write_0'),
            types.InlineKeyboardButton(text='1️⃣', callback_data='write_1'),
            types.InlineKeyboardButton(text='2️⃣', callback_data='write_2'),
        ],
        [
            types.InlineKeyboardButton(text='3️⃣', callback_data='write_3'),
            types.InlineKeyboardButton(text='4️⃣', callback_data='write_4'),
            types.InlineKeyboardButton(text='5️⃣', callback_data='write_5'),
        ],
        [
            types.InlineKeyboardButton(text='6️⃣', callback_data='write_6'),
            types.InlineKeyboardButton(text='7️⃣', callback_data='write_7'),
            types.InlineKeyboardButton(text='8️⃣', callback_data='write_8'),
        ],
        [
            types.InlineKeyboardButton(text='⬅️', callback_data='remove'),
            types.InlineKeyboardButton(text='9️⃣', callback_data='write_9'),
            types.InlineKeyboardButton(text='✅', callback_data='ready'),
        ]
    ]
)


@dp.message_handler(commands='start')
async def on_s(msg: types.Message):
    if CodeInput.data.get(msg.chat.id):
        CodeInput.data.pop(msg.chat.id)
    await msg.answer('Код:', reply_markup=kb)


@dp.callback_query_handler(text_startswith='write_')
async def on_c(call: types.CallbackQuery):
    now = CodeInput.data.get(call.from_user.id)
    code = call.data.split('_')[1]
    if not now:
        CodeInput.data.update({call.from_user.id: code})
        await call.message.edit_text(f'Код: {CodeInput.data.get(call.from_user.id)}',
                                     reply_markup=kb)
    else:
        if len(now) >= 5:
            await call.answer('Нажмите на ✅ для продолжения')
            return

        CodeInput.data.update({call.from_user.id: now + code})
        await call.message.edit_text(f'Код: {CodeInput.data.get(call.from_user.id)}',
                                     reply_markup=kb)


@dp.callback_query_handler(text_startswith='remove')
async def on_1c(call: types.CallbackQuery):
    now = CodeInput.data.get(call.from_user.id)
    if not now:
        await call.answer()
        return
    CodeInput.data.update({call.from_user.id: now[:-1]})
    await call.message.edit_text(f'Код: {CodeInput.data.get(call.from_user.id)}',
                                 reply_markup=kb)


executor.start_polling(dp)
