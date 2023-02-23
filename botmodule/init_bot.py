import os
import sys
import time
import subprocess
from loguru import logger
from libs.cleaner import ConfigManager


def check_init():
    dirs = os.listdir()
    if "clash" in dirs and "logs" in dirs and "results" in dirs:
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


check_init()

# 获取远程仓库的最新提交哈希
latest_version_hash = ""
try:
    output = subprocess.check_output(['git', 'log']).decode().strip()
    # 解析输出，提取最新提交的哈希值
    for line in output.split("\n"):
        if "commit" in line:
            latest_version_hash = line.split()[1][:7]
            break
except Exception as e:
    logger.warning(str(e))
    latest_version_hash = "Unavailable"

logger.add("./logs/fulltclash_{time}.log", rotation='7 days')
config = ConfigManager()
botconfig = config.getBotconfig()
api_id = botconfig.get('api_id', None)
api_hash = botconfig.get('api_hash', None)
bot_token = botconfig.get('bot_token', None)
clash_path = config.get_clash_path()  # 为clash核心运行路径, Windows系统需要加后缀名.exe
clash_work_path = config.get_clash_work_path()  # clash工作路径
corenum = config.config.get('clash', {}).get('core', 1)
admin = config.getAdmin()  # 管理员
config.add_user(admin)
config.reload()
USER_TARGET = config.getuser()  # 这是用户列表，从配置文件读取
logger.info("管理员名单加载:" + str(admin))
# 你的机器人的用户名
USERNAME = "@xxxx_bot"
port = config.get_proxy_port()
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
        logger.info("当前代理设置为: " + proxy_host + ":" + proxy_port + "\n" + "用户名：" + proxy_username + "密码：" + proxy_password)
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
if port:
    logger.warning("当前使用旧版代理方案，今后可能会废弃proxyport该键值对，建议使用新版方案: proxy键值对")
    proxies = {
        "scheme": "socks5",  # "socks4", "socks5" and "http" are supported
        "hostname": "127.0.0.1",
        "port": port
    }
elif proxy_host and proxy_port and proxy_username and proxy_password:
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
# 如果找不到管理员，程序会被强制退出。
if admin is None:
    logger.error("获取管理员失败，将在5s后退出")
    time.sleep(5)
    sys.exit(1)

logger.info("配置已加载, Telegram bot程序正在运行...")

# 启动器
pystr = "python" if sys.platform == "win32" else "python3"
command = fr"{pystr} clash.py"
subp = subprocess.Popen(command.split(), encoding="utf-8")


def reloadUser():
    global USER_TARGET
    config.reload(issave=False)
    USER_TARGET = config.getuser()
    return USER_TARGET
