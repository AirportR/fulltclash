import subprocess
import sys
import time
from loguru import logger
from libs.cleaner import ConfigManager

logger.add("./logs/fulltclash_{time}.log", rotation='7 days')
config = ConfigManager()
USER_TARGET = config.getuser()  # 这是用户列表，从配置文件读取
clash_path = config.get_clash_path()  # 为clash核心运行路径, Windows系统需要加后缀名.exe
clash_work_path = config.get_clash_work_path()  # clash工作路径
admin = config.getAdmin()  # 管理员
logger.info("管理员名单加载:" + str(admin))
# 你的机器人的用户名
USERNAME = "@AirportRoster_bot"
port = config.get_proxy_port()
# 如果是在国内环境，则需要代理环境以供程序连接上TG
if port:
    proxies = {
        "scheme": "socks5",  # "socks4", "socks5" and "http" are supported
        "hostname": "127.0.0.1",
        "port": port
    }
else:
    proxies = None
# 如果找不到管理员，程序会被强制退出。
if admin is None:
    logger.error("获取管理员失败，将在5s后退出")
    time.sleep(5)
    sys.exit(1)

logger.info("配置已加载")
# 启动了一个clash常驻进程
command = fr"{clash_path} -f {'./clash/proxy.yaml'} -d {clash_work_path}"
subp = subprocess.Popen(command.split(), encoding="utf-8")
time.sleep(2)
test_members = 0  # 正在测试的成员，如果为零则停止测试，否则一直测试
logger.info("程序已启动!")
