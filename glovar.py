import tzlocal
from pyrogram import Client
from loguru import logger
from botmodule import init_bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from utils import cron_delete_message as cdm
from utils import cron_edit_message as cem

bot_token = init_bot.bot_token
# 项目版本号
__version__ = '3.5.7'
# 客户端
app = Client("my_bot",
             api_id=init_bot.api_id,
             api_hash=init_bot.api_hash,
             bot_token=bot_token,
             proxy=init_bot.proxies,
             app_version=__version__,
             ipv6=False
             )
app2 = Client("my_user",
              api_id=init_bot.api_id,
              api_hash=init_bot.api_hash,
              proxy=init_bot.proxies,
              app_version=__version__,
              ipv6=False
              )
scheduler = AsyncIOScheduler(timezone=str(tzlocal.get_localzone()))
scheduler.start()
print("""# --------------------------- [ Start bot AsyncIOScheduler Successful ] ---------------------------- # """)
scheduler.add_job(cdm, IntervalTrigger(seconds=10, timezone=str(tzlocal.get_localzone())),
                  id='delete1', name="Delete the telegram message", args=(app,))
scheduler.add_job(cem, IntervalTrigger(seconds=5, timezone=str(tzlocal.get_localzone())),
                  id='edit1', name="Edit the telegram message", args=(app,))


# ---------------------------- [ Set bot Commands] ---------------------------- #
# def set_commands():
#     url = f'https://api.telegram.org/bot{bot_token}/setMyCommands'
#     commands = [
#         {
#             'command': 'help',
#             'description': '/help & /start [游客] 获取帮助菜单'
#         },
#         {
#             'command': 'version',
#             'description': f'[游客]输 出版本信息({__version__})'
#         },
#         {
#             'command': 'analyze',
#             'description': '[用户] 进行节点链路拓扑测试'
#         },
#         {
#             'command': 'test',
#             'description': '[用户] 进行流媒体测试'
#         },
#         {
#             'command': 'speed',
#             'description': '[用户] 进行速度测试'
#         },
#         {
#             'command': 'invite',
#             'description': '[用户] 临时邀请一个目标进行测试（匿名无法生效）'
#         }
#     ]
#     data = {
#         'commands': commands
#     }
#     r = requests.post(url, json=data)
#     if r.status_code == 200:
#         logger.info('Commands set successfully!')
#     else:
#         logger.error(f"Request failed with status code: {r.status_code}")
#     print("""# ---------------------------- [ Set bot Commands Successful ] ---------------------------- #   """)

# ---------------------------- [ Print the bot ] ---------------------------- #
def bot_info(_app):
    bot_me = _app.get_me()
    logger.info('>> Bot Started')
    logger.info(f'>> Bot ID: {bot_me.id} Username: @{bot_me.username}')
    print("""# ---------------------------- [ Start the bot ] ---------------------------- #   """)
    # r = requests.get(
    #     f"https://api.telegram.org/bot{bot_token}/getme")
    # r = json.loads(r.text)
    # r = r["result"]
    # if not r["can_join_groups"]:
    #     logger.error('bot cannot be added to group, please check private settings from @botfather.')
    # else:
    #     logger.info('Congratulations, bot can be added to group !')
    # if not r["can_read_all_group_messages"]:
    #     logger.error(f'bot does not have access to message, please check private settings from @BotFather.')
    # else:
    #     logger.info(f'Congratulations, bot have access to message !')
    print("""# ---------------------------- [ Check Bot Successful ] ---------------------------- #   """)
