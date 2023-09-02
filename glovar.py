import time

import tzlocal
from pyrogram import Client
from loguru import logger
from botmodule import init_bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from utils import cron_delete_message as cdm
from utils import cron_edit_message as cem

program_run_time = time.time()

bot_token = init_bot.bot_token
bot_config = init_bot.config
BUILD_TOKEN = init_bot.config.getBuildToken()
userbot_config = bot_config.config.get('userbot', {})
# 项目版本号
__version__ = '3.6.0'
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
if userbot_config.get('enable', False):
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
    bot_me = _app.get_me()
    logger.info('>> Bot Started')
    logger.info(f'>> Bot ID: {bot_me.id} Username: @{bot_me.username}')
    if _app2 is not None:
        bot_me2 = _app2.get_me()
        whitelist = userbot_config.get('whitelist', [])
        userbot_config['id'] = bot_me2.id
        if bot_me.id not in whitelist:
            whitelist.append(bot_me.id)
        userbot_config['whitelist'] = whitelist
        bot_config.yaml['userbot'] = userbot_config
        bot_config.reload()
        logger.info('>> UserBot enable')
        logger.info(f'>> UserBot ID: {bot_me2.id} Username: @{bot_me2.username}')

    print("""# ---------------------------- [ Start the bot ] ---------------------------- #   """)
    print("""# ---------------------------- [ Check Bot Successful ] ---------------------------- #   """)
