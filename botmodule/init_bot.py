from loguru import logger
from utils.cleaner import config
from utils.init import check_init, Init, check_args

admin = config.getAdmin()  # 管理员


def parse_bot_proxy():
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


logger.add("./logs/fulltclash_{time}.log", rotation='7 days')
check_args()
check_init()

# 获取远程仓库的最新提交哈希
latest_version_hash = Init.init_commit_string()
botconfig = config.getBotconfig()
api_id = botconfig.get('api_id', None)
api_hash = botconfig.get('api_hash', None)
bot_token = botconfig.get('bot_token', None)
USER_TARGET = config.getuser()  # 这是用户列表，从配置文件读取
BOT_PROXY = parse_bot_proxy()

logger.info("配置已加载, Telegram bot程序开始运行...")


def reloadUser():
    global USER_TARGET
    config.reload(issave=False)
    USER_TARGET = config.getuser()
    return USER_TARGET
