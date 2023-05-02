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
app2 = None
if init_bot.config.config.get('userbot', {}).get('enable', False):
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


# ---------------------------- [ Print the bot ] ---------------------------- #
def bot_info(_app, _app2):
    if _app2 is not None:
        bot_me2 = _app2.get_me()
        logger.info('>> UserBot enable')
        logger.info(f'>> UserBot ID: {bot_me2.id} Username: @{bot_me2.username}')
    bot_me = _app.get_me()
    logger.info('>> Bot Started')
    logger.info(f'>> Bot ID: {bot_me.id} Username: @{bot_me.username}')
    print("""# ---------------------------- [ Start the bot ] ---------------------------- #   """)
    print("""# ---------------------------- [ Check Bot Successful ] ---------------------------- #   """)
