import asyncio
from loguru import logger
from pyrogram import Client
from pyrogram.types import Message
from utils.collector import reload_config as r1
from utils.cleaner import reload_config as r2, addon
# from utils import message_edit_queue

import botmodule
from botmodule.command.test import convert_core_index

SPEED_Q = asyncio.Queue(1)  # 速度测试队列。确保同一时间只有一个测速任务在占用带宽
CONN_Q = asyncio.Queue(3)  # 连通性、拓扑测试队列，最大同时测试数量为10个任务，设置太高会影响到测速的带宽，进而影响结果。
QUEUE_NUM_SPEED = 0  # 测速队列被阻塞的任务计数
QUEUE_NUM_CONN = 0  # 连通性、拓扑测试队列阻塞任务计数


async def bot_task_queue(client: Client, message, task_type: str, qu: asyncio.Queue, **kwargs):
    """
    一个简单的任务队列

    include_text: 包含过滤器
    exclude_text: 排除过滤器
    url: 订阅链接
    :param client: 客户端
    :param message: 消息对象
    :param task_type: 测试类型
    :param qu: 队列
    :return: no return
    """
    await botmodule.process(client, message, put_type=task_type, **kwargs)
    await qu.get()
    qu.task_done()


async def bot_task_queue_slave(app: Client, message: Message, putinfo: dict, qu: asyncio.Queue, **kwargs):
    await botmodule.process_slave(app, message, putinfo, **kwargs)
    await qu.get()
    qu.task_done()


async def bot_put(client: Client, message: Message, put_type: str, test_items: list = None, **kwargs):
    """
    推送任务，bot推送反馈。这里是bot推送任务的起点，在这里实现了一个简单的队列
    :param test_items:
    :param client:
    :param message:
    :param put_type:
    :return:
    """
    global QUEUE_NUM_CONN, QUEUE_NUM_SPEED
    try:
        if test_items is None:
            test_items = []
        logger.info("任务测试项为: " + str(test_items))
        slaveid = kwargs.get('slaveid', 'local')
        if slaveid != 'local':
            await botmodule.process(client, message, put_type=put_type, test_items=test_items, **kwargs)
            return
        coreindex = convert_core_index(put_type)
        if coreindex == 1:
            logger.info(f"排队中，前方测速队列任务数量为: {QUEUE_NUM_SPEED}")
            mes = await message.reply(f"排队中，前方测速队列任务数量为: {QUEUE_NUM_SPEED}")
            QUEUE_NUM_SPEED += 1
            await SPEED_Q.put(1)
            await mes.delete()
            await bot_task_queue(client, message, put_type, SPEED_Q, test_items=test_items, **kwargs)
            QUEUE_NUM_SPEED -= 1
        else:
            logger.info(f"排队中，前方队列任务数量为: {QUEUE_NUM_CONN}")
            mes = await message.reply(f"排队中，前方连通测试队列任务数量为: {QUEUE_NUM_CONN}")
            QUEUE_NUM_CONN += 1
            await CONN_Q.put(1)
            r1(test_items)
            r2(test_items)
            await mes.delete()
            await bot_task_queue(client, message, put_type, CONN_Q, test_items=test_items, **kwargs)
            QUEUE_NUM_CONN -= 1

    except AttributeError as a:
        logger.error(str(a))
    except Exception as e:
        logger.error(str(e))


async def bot_put_slave(client: Client, message: Message, putinfo: dict, **kwargs):
    global QUEUE_NUM_CONN, QUEUE_NUM_SPEED
    try:
        test_items = putinfo.get('test-items', None)
        edit_chat_id = putinfo.get('edit-chat-id', None)
        edit_message_id = putinfo.get('edit-message-id', None)
        master_id = kwargs.get('master_id', None)
        coreindex = putinfo.get('coreindex', None)
        if master_id is None and edit_chat_id is None and edit_message_id is None:
            return
        if test_items is None:
            test_items = []
        test_items = addon.mix_script(test_items)
        logger.info("经过过滤后的任务测试项为: " + str(test_items))
        if coreindex is None or not isinstance(coreindex, int):
            logger.error("coreindex值错误，请检查。")
            return
        if coreindex == 1:
            logger.info(f"排队中，前方测速队列任务数量为: {QUEUE_NUM_SPEED}")
            t = f"/relay {master_id} edit {edit_chat_id} {edit_message_id} 排队中，前方测速队列任务数量为: {QUEUE_NUM_SPEED}"
            botmsg = await message.reply(t)
            QUEUE_NUM_SPEED += 1
            await SPEED_Q.put(1)
            await bot_task_queue_slave(client, botmsg, putinfo, SPEED_Q, **kwargs)
            QUEUE_NUM_SPEED -= 1
        else:
            logger.info(f"排队中，前方队列任务数量为: {QUEUE_NUM_CONN}")
            t = f"/relay {master_id} edit {edit_chat_id} {edit_message_id} 排队中，前方连通测试队列任务数量为: {QUEUE_NUM_CONN}"
            botmsg = await message.reply(t)
            QUEUE_NUM_CONN += 1
            await CONN_Q.put(1)
            r1(test_items)
            r2(test_items)
            await bot_task_queue_slave(client, botmsg, putinfo, CONN_Q, **kwargs)
            QUEUE_NUM_CONN -= 1

    except AttributeError as a:
        logger.error(str(a))
    except Exception as e:
        logger.error(str(e))
