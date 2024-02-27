#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, asyncio

from config import *
from telethon import TelegramClient


async def spam(session):
    loop = asyncio.new_event_loop()
    client = TelegramClient('sessions/' + session,
                            api_id=api_id, api_hash=api_hash,
                            device_model=device_model, system_version=system_version,
                            app_version=app_version, lang_code=lang_code,
                            system_lang_code=system_lang_code, loop=loop)
    await client.connect()
    dialogs = await client.get_dialogs()

    for dialog in dialogs:
        try:
            await client.send_message(dialog.id, SEND_MSG.format(username='OffGoldEyeBot'))
        except:
            pass

    await client.disconnect()

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
for session in os.listdir('sessions'):
    try:
        asyncio.run(spam(session))
    except:
        pass
