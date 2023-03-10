import time
import asyncio
import tzlocal
from loguru import logger

from glovar import app
import pyrogram.errors.exceptions.forbidden_403
import pyrogram.errors.exceptions.bad_request_400

from botmodule.utils import message_delete_queue
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler(timezone=str(tzlocal.get_localzone()))


async def cron_delete_message():
    # logger.info('Start Cron Delete Message')
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
                except pyrogram.errors.exceptions.forbidden_403.MessageDeleteForbidden as e:
                    logger.error(e)
                    continue
                except Exception as e:
                    logger.error(f'1. Delete Message: {e}')
                    continue
                logger.info(f'于: {message.chat.title} ({delete_message[0]}) 删除ID: {message.id} 成功.')
            else:
                message_delete_queue.put_nowait(delete_message)
        except Exception as e:
            logger.error(f'2. Delete Message: {e}')
            continue

# scheduler.add_job(cron_delete_message, 'interval', seconds=2)
