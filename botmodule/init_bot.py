import asyncio
import os
import sys
# subprocess 模块用于启动子进程，并与其通信
# 注意：使用 subprocess 时要小心不要执行不可信的输入
from subprocess import check_output

from loguru import logger

from utils.clash import check_port, start_fulltclash
from utils.cleaner import ConfigManager
from utils.safe import gen_key

config = ConfigManager()  # 配置加载
admin = config.getAdmin()  # 管理员
config.add_user(admin)  # 管理员同时也是用户
config.reload()


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

    args = parser.parse_args()
    if args.r:
        if os.path.exists("./my_bot.session"):
            logger.info("检测到启用session文件覆写选项")
            try:
                os.remove("my_bot.session")
                logger.info("已移除my_bot.session")
            except Exception as e2:
                logger.error(f"session文件移除失败：{e2}")

    if args.admin:
        adminlist = str(args.admin).split(",")
        logger.info(f"即将添加管理员：{adminlist}")
        config.add_admin(adminlist)
        config.reload()
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
    if "clash" in dirs and "logs" in dirs and "results" in dirs and 'key' in dirs:
        return
    logger.info("检测到初次使用，正在初始化...")
    if not os.path.isdir('clash'):
        os.mkdir("clash")
        logger.info("创建文件夹: clash 用于保存订阅")
    if not os.path.isdir('logs'):
        os.mkdir("logs")
        logger.info("创建文件夹: logs 用于保存日志")
    if not os.path.isdir('results'):
        os.mkdir("results")
        logger.info("创建文件夹: results 用于保存测试结果")
    if not os.path.isdir('key'):
        os.mkdir("key")
        logger.info("创建文件夹: key 用于保存公钥")
    dirs = os.listdir('./key')
    if "fulltclash-public.pem" in dirs:
        return
    if "fulltclash-private.pem" in dirs:
        return
    logger.info("正在初始化公私钥")
    gen_key()


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


check_args()
check_init()
# 获取远程仓库的最新提交哈希
latest_version_hash = check_version()

logger.add("./logs/fulltclash_{time}.log", rotation='7 days')

botconfig = config.getBotconfig()
api_id = botconfig.get('api_id', None)
api_hash = botconfig.get('api_hash', None)
bot_token = botconfig.get('bot_token', None)
clash_path = config.get_clash_path()  # 为clash核心运行路径, Windows系统需要加后缀名.exe
clash_work_path = config.get_clash_work_path()  # clash工作路径
corenum = min(config.config.get('clash', {}).get('core', 1), 128)

USER_TARGET = config.getuser()  # 这是用户列表，从配置文件读取
logger.info("管理员名单加载:" + str(admin))
# 你的机器人的用户名
USERNAME = "@FullTclashBot"
port = config.get_proxy_port()
proxy_subprocess = None
try:
    _proxy = config.get_bot_proxy(isjoint=False).split(':')
    proxy_host = _proxy[0]
    proxy_port = _proxy[1]
    proxy_username = None
    proxy_password = None
    lenproxy = len(_proxy)
    if lenproxy < 3:
        logger.info("当前代理设置为: " + proxy_host + ":" + proxy_port)
    else:
        proxy_username = _proxy[2]
        proxy_password = _proxy[3]
        logger.info(
            "当前代理设置为: " + proxy_host + ":" + proxy_port + "\n" + "用户名：" + proxy_username + "密码：" + proxy_password)
except AttributeError as attr:
    logger.info(str(attr))
    proxy_host = None
    proxy_port = None
    proxy_username = None
    proxy_password = None
except Exception as e:
    logger.error(str(e))
    proxy_host = None
    proxy_port = None
    proxy_username = None
    proxy_password = None
# 如果是在国内环境，则需要代理环境以供程序连接上TG

if proxy_host and proxy_port and proxy_username and proxy_password:
    proxies = {
        "scheme": "socks5",  # "socks4", "socks5" and "http" are supported
        "hostname": proxy_host,
        "port": int(proxy_port),
        "username": f"{proxy_username}",
        "password": f"{proxy_password}"
    }
elif proxy_host and proxy_port:
    proxies = {
        "scheme": "socks5",  # "socks4", "socks5" and "http" are supported
        "hostname": proxy_host,
        "port": int(proxy_port)
    }
else:
    proxies = None

logger.info("配置已加载, Telegram bot程序开始运行...")


def start_clash():
    # 端口检查
    global proxy_subprocess
    loop = asyncio.get_event_loop()
    start_port = config.config.get('clash', {}).get('startup', 11220)
    port_list = [str(start_port + i * 2) for i in range(corenum)]
    res2 = loop.run_until_complete(check_port(start_port - 1, start_port + 1 + corenum * 2))
    if res2:
        logger.warning("端口检查中发现已有其他进程占用了端口，请更换端口,否则测试可能会出现不可预知的错误。(亦或者是您分开启动？)")
        return
    # if config.config.get('clash', {}).get('auto-start', False):
    print("开始启动clash core")
    if sys.platform != "win32":
        try:
            status = os.system(f"chmod +x {clash_path}")
            if status != 0:
                raise OSError(f"Failed to execute command: chmod +x {clash_path}")
        except OSError as o:
            print(o)
    proxy_subprocess = start_fulltclash(port_list)


start_clash()


def reloadUser():
    global USER_TARGET
    config.reload(issave=False)
    USER_TARGET = config.getuser()
    return USER_TARGET
