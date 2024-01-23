import asyncio
import os
import sys
from subprocess import check_output

from loguru import logger
from utils.cleaner import config

admin = config.getAdmin()  # 管理员
config.add_user(admin)  # 管理员同时也是用户
config.reload()


def check_permission():
    if sys.platform != "win32":
        try:
            status = os.system(f"chmod +x {clash_path}")
            if status != 0:
                raise OSError(f"Failed to execute command: chmod +x {clash_path}")
        except OSError as o:
            print(o)


def check_args():
    import argparse
    help_text_socks5 = "设置socks5代理，bot代理使用的这个\n格式--> host:端口:用户名:密码\t用户名和密码可省略"
    help_text_http = "设置HTTP代理,拉取订阅用的。\n格式--> 用户名:密码@host:端口\t@符号前面的用户名和密码如果不设置可省略"
    help_f = "强制覆盖原先的mybot.session文件，重新生成"
    parser = argparse.ArgumentParser(description="FullTClash命令行快速启动，其中api_id,api_hash,bot_token要么不填，要么全部填完")
    parser.add_argument("-r", action='store_true', help=help_f)
    parser.add_argument("-ah", "--api-hash", required=False, type=str, help="自定义api-hash")
    parser.add_argument("-ai", "--api-id", required=False, type=int, help="自定义api-id")
    parser.add_argument("-b", "--bot-token", required=False, type=str, help="自定义bot-token")
    parser.add_argument("-ps5", "--proxy-socks5", required=False, type=str, help=help_text_socks5)
    parser.add_argument("-http", "--proxy-http", required=False, type=str, help=help_text_http)
    parser.add_argument("-su", "--admin", required=False, help="设置bot的管理员，多个管理员以 , 分隔")
    parser.add_argument("-d", "--path", required=False, type=str, help="设置代理客户端路径")

    args = parser.parse_args()
    if args.r:
        if os.path.exists("./my_bot.session"):
            logger.info("检测到启用session文件覆写选项")
            try:
                os.remove("my_bot.session")
                logger.info("已移除my_bot.session")
            except Exception as e2:
                logger.error(f"session文件移除失败：{e2}")
    if args.path:
        config.yaml['clash'] = config.config.get('clash', {}).setdefault('path', str(args.d))
    if args.admin:
        adminlist = str(args.admin).split(",")
        logger.info(f"即将添加管理员：{adminlist}")
        config.add_admin(adminlist)
    if args.proxy_http:
        config.yaml['proxy'] = str(args.proxy_http)
        logger.info("从命令行参数中设置HTTP代理")
    if args.api_hash and args.api_id and args.bot_token:
        tempconf = {
            "api_hash": args.api_hash,
            "api_id": args.api_id,
            "bot_token": args.bot_token,
            "proxy": args.proxy_socks5,
        }
        bot_conf = config.getBotconfig()
        bot_conf.update(tempconf)
        config.yaml['bot'] = bot_conf
        logger.info("从命令行参数中设置api_hash,api_id,bot_token")
        if args.proxy_socks5:
            logger.info("从命令行参数中设置bot的socks5代理")
    i = config.reload()
    if i:
        logger.info("已覆写配置文件。")
    else:
        logger.warning("覆写配置失败！")


def check_init():
    if config.getClashBranch() == 'meta':
        logger.info('✅检测到启用clash.meta系内核配置，请自行配置更换成fulltclash-meta代理客户端（默认为原生clash内核）。')
    emoji_source = config.config.get('emoji', {}).get('emoji-source', 'TwemojiLocalSource')
    if config.config.get('emoji', {}).get('enable', True) and emoji_source == 'TwemojiLocalSource':
        from utils.emoji_custom import TwemojiLocalSource
        if not os.path.isdir('./resources/emoji/twemoji'):
            twemoji = TwemojiLocalSource()
            logger.info("检测到未安装emoji资源包，正在初始化本地emoji...")
            asyncio.get_event_loop().run_until_complete(twemoji.download_emoji(proxy=config.get_proxy()))
            if twemoji.init_emoji(twemoji.savepath):
                logger.info("初始化emoji成功")
            else:
                logger.warning("初始化emoji失败")
    dirs = os.listdir()
    if "logs" in dirs and "results" in dirs:
        return
    logger.info("检测到初次使用，正在初始化...")
    if not os.path.isdir('logs'):
        os.mkdir("logs")
        logger.info("创建文件夹: logs 用于保存日志")
    if not os.path.isdir('results'):
        os.mkdir("results")
        logger.info("创建文件夹: results 用于保存测试结果")
    check_permission()


def check_version() -> str:
    _latest_version_hash = ""
    try:
        output = check_output(['git', 'log'], shell=False, encoding="utf-8").strip()
        # 解析输出，提取最新提交的哈希值
        for line in output.split("\n"):
            if "commit" in line:
                _latest_version_hash = line.split()[1][:7]
                break
    except Exception as e0:
        logger.info("可能不是通过git拉取源码，因此version将无法查看提交哈希。")
        logger.warning(str(e0))
        _latest_version_hash = "Unavailable"
    return _latest_version_hash


def parse_proxy():
    _proxies = None
    try:
        _proxy = config.get_bot_proxy(isjoint=False).split(':')
        p_host = _proxy[0]
        p_port = _proxy[1]
        p_username = None
        p_password = None
        lenproxy = len(_proxy)
        if lenproxy < 3:
            logger.info("当前代理设置为：" + p_host + ":" + p_port)
        else:
            p_username = _proxy[2]
            p_password = _proxy[3] if lenproxy > 3 else ''
            logger.info(f"当前代理设置为： {p_host}:{p_port} 用户名：{p_username} 密码：{p_password}")
        if p_host and p_port and p_username and p_password:
            _proxies = {
                "scheme": "socks5",  # "socks4", "socks5" and "http" are supported
                "hostname": p_host,
                "port": int(p_port),
                "username": f"{p_username}",
                "password": f"{p_password}"
            }
        elif p_host and p_port:
            _proxies = {
                "scheme": "socks5",  # "socks4", "socks5" and "http" are supported
                "hostname": p_host,
                "port": int(p_port)
            }
    except (AttributeError, Exception) as err:
        logger.info(str(err))
        _proxies = None
    finally:
        return _proxies


# 获取远程仓库的最新提交哈希
latest_version_hash = check_version()

logger.add("./logs/fulltclash_{time}.log", rotation='7 days')

botconfig = config.getBotconfig()
api_id = botconfig.get('api_id', None)
api_hash = botconfig.get('api_hash', None)
bot_token = botconfig.get('bot_token', None)
clash_path = config.get_clash_path()  # 为代理客户端运行路径
# clash_work_path = config.get_clash_work_path()  # clash工作路径
corenum = min(config.config.get('clash', {}).get('core', 1), 128)

USER_TARGET = config.getuser()  # 这是用户列表，从配置文件读取
logger.info("管理员名单加载:" + str(admin))
check_args()
check_init()
proxies = parse_proxy()
logger.info("配置已加载, Telegram bot程序开始运行...")


def reloadUser():
    global USER_TARGET
    config.reload(issave=False)
    USER_TARGET = config.getuser()
    return USER_TARGET
