import time
import asyncio

from loguru import logger
from pyrogram import Client
from pyrogram.errors.exceptions import forbidden_403

from utils.cron.utils import message_delete_queue, message_edit_queue


async def cron_edit_message(app: Client):
    edit_messages = []
    while True:
        try:
            edit_messages.append(message_edit_queue.get_nowait())
        except asyncio.queues.QueueEmpty:
            break
    for edit_message in edit_messages:
        try:
            message = None
            if edit_message[0] and edit_message[1]:
                message = await app.get_messages(edit_message[0], edit_message[1])
            if message is None:
                continue
            if message.date is None:
                continue
            if int(message.date.timestamp()) + edit_message[3] < int(time.time()):
                try:
                    IKM = edit_message[4] if len(edit_message) > 4 else None
                    await app.edit_message_text(edit_message[0], edit_message[1], edit_message[2], reply_markup=IKM)
                except forbidden_403.MessageDeleteForbidden:
                    continue
                except Exception as e:
                    logger.error(f'Edit Message: {e}')
                    continue
                # logger.info(f'于: {message.chat.title} ({edit_message[0]}) 编辑ID: {message.id} 成功.')
            else:
                message_edit_queue.put_nowait(edit_message)
        except Exception as e:
            logger.error(f'Edit Message: {e}')
            continue


async def cron_delete_message(app: Client):
    delete_messages = []
    while True:
        try:
            delete_messages.append(message_delete_queue.get_nowait())
        except asyncio.queues.QueueEmpty:
            break

    for delete_message in delete_messages:
        try:
            message = await app.get_messages(delete_message[0], delete_message[1])
            if int(message.date.timestamp()) + delete_message[2] < int(time.time()):
                try:
                    await app.delete_messages(delete_message[0], delete_message[1], revoke=False)
                except forbidden_403.MessageDeleteForbidden:
                    continue
                except Exception as e:
                    logger.warning(str(e))
                    continue
                logger.info(f'消息删除触发器于: {message.chat.title} ({delete_message[0]}) 删除ID: {message.id} 成功.')
            else:
                message_delete_queue.put_nowait(delete_message)
        except Exception as e:
            logger.warning(str(e))
            continue
