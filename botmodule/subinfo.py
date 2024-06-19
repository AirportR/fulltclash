import hashlib
import time
from loguru import logger
from pyrogram.enums import ParseMode
from pyrogram.errors import RPCError
from utils.cleaner import geturl, ArgCleaner
from utils.collector import SubCollector
from utils.check import get_telegram_id_from_message as get_id
from utils.check import check_user
from utils import message_delete_queue as mdq
from botmodule.init_bot import config, admin


async def getSubInfo(_, message):
    ID = get_id(message)
    arg = ArgCleaner.getarg(str(message.text))
    call_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
    try:
        if len(arg) == 1:
            b1 = await message.reply("使用方法: /traffic & /subinfo & /流量查询 + <订阅链接> & <订阅名>")
            mdq.put(b1)
            return
        back_message = await message.reply("正在查询流量信息...")  # 发送提示
        url = geturl(str(message.text))
        no_url = False
        subname = arg[1] if len(arg) > 1 else ""
        if not url:
            # 尝试从配置文件中获取订阅
            pwd = arg[2] if len(arg) > 2 else arg[1]
            subinfo = config.get_sub(arg[1])
            if not subinfo:
                await back_message.edit_text("❌未找到该订阅")
                mdq.put(back_message, 5)
                return
            subpwd = subinfo.get('password', '')
            subowner = subinfo.get('owner', '')
            share_list = subinfo.get("share", [])
            url = str(subinfo.get('url', ''))
            if not isinstance(share_list, list):
                share_list = []
            if await check_user(message, admin, isalert=False):
                # 管理员至高权限
                no_url = True
            else:
                if subowner and subowner == ID:
                    if hashlib.sha256(pwd.encode("utf-8")).hexdigest() == subpwd:
                        no_url = True
                    else:
                        await back_message.edit_text("❌密码错误，请检查后重试。")
                        return
                elif str(ID) in share_list:
                    no_url = True
                else:
                    await back_message.edit_text("❌身份ID不匹配，您无权查看该订阅流量信息。")
                    return
        subcl = SubCollector(url)
        subcl.cvt_enable = False
        subinfo = await subcl.getSubTraffic()
        site_name = await subcl.getSiteTitle()
        if not subinfo:
            await back_message.edit_text("此订阅无法获取流量信息.")
            return
        days_diff = subinfo[5] if len(subinfo) > 5 else ""
        if days_diff:
            days_diff = f"({days_diff}天)"
        rs = subinfo[3] - subinfo[2]  # 剩余流量
        subinfo_text = f"""
⬆️已用上行：{round(subinfo[0], 3)} GB
⬇️已用下行：{round(subinfo[1], 3)} GB
🚗总共使用：{round(subinfo[2], 3)} GB
⏳剩余流量：{round(rs, 3)} GB
💧总流量：{round(subinfo[3], 3)} GB
⏱️过期时间：{subinfo[4]} {days_diff}
🔍查询时间：{call_time}
        """
        if no_url:
            subinfo_text = f"☁️订阅名称：{subname}" + subinfo_text
        else:
            subinfo_text = f"☁️订阅链接：{url}" + subinfo_text
        site_name = f"✈️机场名：{site_name}\n" if site_name else "✈️机场名：未知\n"
        subinfo_text = site_name + subinfo_text
        await back_message.edit_text(subinfo_text, parse_mode=ParseMode.DISABLED)
    except RPCError as r:
        logger.error(str(r))
