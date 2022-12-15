from loguru import logger
from pyrogram.errors import RPCError
from libs.cleaner import geturl
from libs.collector import SubCollector


async def getSubInfo(_, message):
    try:
        back_message = await message.reply("正在查询流量信息...")  # 发送提示
        text = str(message.text)
        url = geturl(text)
        if not url:
            await back_message.edit_text("使用方法: /traffic & /subinfo & /流量查询 + <订阅链接>")
            return
        subcl = SubCollector(url)
        subcl.cvt_enable = False
        subinfo = await subcl.getSubTraffic()
        if subinfo:
            rs = subinfo[3] - subinfo[2]  # 剩余流量
            subinfo_text = f"""
☁️订阅链接：{url}
⬆️已用上行：{subinfo[0]} GB
⬇️已用下行：{subinfo[1]} GB
🚗总共使用：{subinfo[2]} GB
⏳剩余流量：{rs} GB
💧总流量：{subinfo[3]} GB
⏱️过期时间：{subinfo[4]}
                """
            await back_message.edit_text(subinfo_text)
        else:
            await back_message.edit_text("此订阅无法获取流量信息")
    except RPCError as r:
        logger.error(str(r))
