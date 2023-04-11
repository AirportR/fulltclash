from pyrogram import Client
from pyrogram.errors import RPCError,BadRequest
import asyncio


async def main():
    print(
        """
        使用指南
        依次输入api_id、api_hash、bot_token
        接下来输入代理相关设置，如果是中国大陆外的机子就不用输，按回车即可。
        proxy_addr 填地址，本地填 127.0.0.1
        proxy_port 填代理端口， clash默认7890，其他自测。
        username 这个是要求你输入一个已存在的TG用户名或者UID，它会尝试给这个用户发一条消息，如果收到了消息，证明session生成成功了，程序结束。
        """
    )
    api_id = str(input("Please enter your api_id:"))
    api_hash = str(input("Please enter your api_hash:"))
    bot_token = str(input("Please enter your bot_token:"))
    proxy_addr = str(input("Please enter your proxy_address(socks5,if you use this program in China):"))
    proxy_port = input("Please enter your proxy_port:")
    master = str(input("Please enter your username:"))
    try:
        if not proxy_addr or not proxy_port:
            proxies = None
        else:
            proxies = {
                "scheme": "socks5",  # "socks4", "socks5" and "http" are supported
                "hostname": proxy_addr,
                "port": int(proxy_port)
            }
    except Exception as e:
        print(e)
        proxies = None
    print("Your api_id is: ", api_id)
    print("Your api_hash is: ", api_hash)
    print("Your bot_token is: ", bot_token)
    if not (len(str(api_id)) and len(api_hash)):
        print("Please enter agian!")
    else:
        print("Starting client...")
        try:
            async with Client("my_bot", proxy=proxies, api_id=api_id, api_hash=api_hash,
                              bot_token=bot_token) as app:
                await app.send_message(master, "嗨, 我在正常工作哦！")
        except BadRequest:
            if master:
                print("你需要主动私聊一次机器人或者该用户名填写错误！")
            else:
                print("未输入用户名，无法确认my_bot.session的有效性!")
        except RPCError as r:
            print(r)


asyncio.run(main())
