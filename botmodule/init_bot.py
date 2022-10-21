import subprocess
import sys
import time
from loguru import logger
from libs.cleaner import ConfigManager

logger.add("./logs/fulltclash_{time}.log", rotation='7 days')
config = ConfigManager()
clash_path = config.get_clash_path()  # 为clash核心运行路径, Windows系统需要加后缀名.exe
clash_work_path = config.get_clash_work_path()  # clash工作路径
admin = config.getAdmin()  # 管理员
config.add_user(admin)
config.reload()
USER_TARGET = config.getuser()  # 这是用户列表，从配置文件读取
logger.info("管理员名单加载:" + str(admin))
# 你的机器人的用户名
USERNAME = "@xxxx_bot"
port = config.get_proxy_port()
try:
    _proxy = config.get_proxy(isjoint=False).split(':')
    proxy_host = _proxy[0]
    proxy_port = _proxy[1]
    logger.info("当前代理设置为: " + proxy_host + ":" + proxy_port)
except AttributeError as attr:
    logger.info(str(attr))
    proxy_host = None
    proxy_port = None
except Exception as e:
    logger.error(str(e))
    proxy_host = None
    proxy_port = None
# 如果是在国内环境，则需要代理环境以供程序连接上TG
if port:
    logger.warning("当前使用旧版代理方案，今后可能会废弃proxyport该键值对，建议使用新版方案: proxy键值对")
    proxies = {
        "scheme": "socks5",  # "socks4", "socks5" and "http" are supported
        "hostname": "127.0.0.1",
        "port": port
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


logger.info("配置已加载, 程序启动中...")
# 启动了一个clash常驻进程
command = fr"{clash_path} -f {'./clash/proxy.yaml'} -d {clash_work_path}"
subp = subprocess.Popen(command.split(), encoding="utf-8")
time.sleep(2)
logger.info("程序已启动!")


def reloadUser():
    global USER_TARGET
    config.reload(issave=False)
    USER_TARGET = config.getuser()
    return USER_TARGET
