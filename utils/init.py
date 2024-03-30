import asyncio
import os
import sys
from pathlib import Path
from subprocess import check_output

from loguru import logger

from utils import cleaner, generate_random_string, websocket, HOME_DIR
from utils.cleaner import unzip, unzip_targz
from utils.collector import get_latest_tag, Download, DownloadError

GCONFIG = cleaner.config


async def check_init():
    check_args()
    check_py_version()
    Init.init_dir()
    await Init.init_proxy_client()
    Init.init_permission()


def check_py_version() -> None:
    if sys.version_info < (3, 9):
        py_url = "https://www.python.org/downloads/"
        logger.info(f"您的Python版本为{sys.version}。\n至少需要Python3.9才能运行此程序。前往: {py_url}下载新版本。")
        sys.exit()


def check_args():
    import argparse
    parser = argparse.ArgumentParser(description="FullTClash-纯后端命令行快速启动")
    parser.add_argument("-b", "--bind", required=False, type=str, help="覆写绑定的外部地址端口，默认为127.0.0.1:8765")
    parser.add_argument("-t", "--token", required=False, type=str, help="Websocket通信Token，也叫做密码，防止不合法的请求。")
    parser.add_argument("-p", "--path", required=False, type=str, help="Websocket连接路径，不设置默认为根路径/ 例： --path YaPyu>hwy<[")
    parser.add_argument("-f", "--buildtoken", required=False, type=str, help="FullTCore代理客户端的buildtoken，不填则为默认值")

    args = parser.parse_args()

    if args.bind:
        bindaddr = str(args.bind)
        wsconf = GCONFIG.config.get('websocket', {})
        wsconf['bindAddress'] = bindaddr
        GCONFIG.yaml['websocket'] = wsconf
        GCONFIG.reload()
        logger.info(f"已覆写监听地址：{bindaddr}")
    wsconf = GCONFIG.config.get('websocket', {})
    if args.token:
        wstoken = str(args.token)
    else:
        wstoken = wsconf.get('token', '')
        if not wstoken:
            wstoken = generate_random_string()
    wsconf['token'] = wstoken
    GCONFIG.yaml['websocket'] = wsconf
    GCONFIG.reload()
    logger.info(f"已覆写Websocket通信Token为: {wstoken}")
    if args.path:
        ws_path = str(args.path)
        wsconf = GCONFIG.config.get('websocket', {})
        wsconf['path'] = ws_path
        GCONFIG.yaml['websocket'] = wsconf
        GCONFIG.reload()
        ws_path2 = websocket.parse_wspath(ws_path)
        logger.info(f"已设置Websocket连接路径为：{ws_path}\r运行时为MD5[ws连接路径]: {ws_path2}")
    if args.buildtoken:
        buildtoken = str(args.buildtoken)
        GCONFIG.yaml['buildtoken'] = buildtoken
        GCONFIG.reload()
        logger.info("已覆写FullTCore编译Token")


class Init:
    repo_owner = "AirportR"
    repo_name = "FullTclash"
    ftcore_owner = repo_owner
    ftcore_name = "FullTCore"

    @staticmethod
    def init_dir():
        dirs = os.listdir(HOME_DIR)
        if "logs" in dirs and "results" in dirs:
            return
        logger.info("检测到初次使用，正在初始化...")
        if not os.path.isdir('logs'):
            os.mkdir("logs")
            logger.info("创建文件夹: logs 用于保存日志")
        if not os.path.isdir('results'):
            os.mkdir("results")
            logger.info("创建文件夹: results 用于保存测试结果")

    @staticmethod
    def init_permission():
        if sys.platform != "win32":
            try:
                status = os.system(f"chmod +x {GCONFIG.get_clash_path()}")
                if status != 0:
                    raise OSError(f"Failed to execute command: chmod +x {GCONFIG.get_clash_path()}")
            except OSError as o:
                print(o)

    @staticmethod
    def init_commit_string():
        _latest_version_hash = ""
        try:
            output = check_output(['git', 'log'], shell=False, encoding="utf-8").strip()
            # 解析输出，提取最新提交的哈希值
            for line in output.split("\n"):
                if "commit" in line:
                    _latest_version_hash = line.split()[1][:7]
                    break
        except Exception as e:
            logger.info(f"可能不是通过git拉取源码，因此version将无法查看提交哈希。{str(e)}")
            _latest_version_hash = "Unknown"
        return _latest_version_hash

    @staticmethod
    async def init_proxy_client():
        """
        自动下载代理客户端FullTCore
        """
        if GCONFIG.get_clash_path() is not None:
            return
        import platform
        tag = await get_latest_tag(Init.ftcore_owner, Init.ftcore_name)
        tag2 = tag[1:] if tag[0] == "v" else tag
        arch = platform.machine().lower()
        if arch == "x86_64":
            arch = "amd64"
        elif arch == "aarch64" or arch == "armv8":
            arch = "arm64"
        elif arch == "x86":
            arch = "i386"
        elif arch == "arm":
            arch = "armv7l"
        suffix = ".tar.gz"
        if sys.platform.startswith('linux'):
            pf = "linux"
        elif sys.platform.startswith('darwin'):
            pf = "darwin"
        elif sys.platform.startswith('win32'):
            pf = "windows"
            suffix = ".zip"
        else:
            logger.info("无法找到FullTCore在当前平台的预编译文件，请自行下载。")
            return

        # https://github.com/AirportR/FullTCore/releases/download/v1.3-meta/FullTCore_1.3-meta_windows_amd64.zip
        base_url = f"https://github.com/{Init.ftcore_owner}/{Init.ftcore_name}"

        download_url = base_url + f"/releases/download/{tag}/FullTCore_{tag2}_{pf}_{arch}{suffix}"
        savename = download_url.split("/")[-1]
        logger.info(f"正在自动为您下载最新版本({tag})的FullTCore: {download_url}")
        savepath = Path(HOME_DIR).joinpath("bin").absolute()
        saved_file = savepath.joinpath(savename)

        try:
            await Download(download_url, savepath, savename).dowload(proxy=GCONFIG.get_proxy())
        except DownloadError:
            logger.info("无法找到FullTCore在当前平台的预编译文件，请自行下载。")
            return
        except (OSError, Exception) as e:
            logger.info(str(e))
            return

        if suffix.endswith("zip"):
            unzip_result = unzip(saved_file, savepath)
        elif suffix.endswith("tar.gz"):
            unzip_result = unzip_targz(saved_file, savepath)
        else:
            unzip_result = False
        if unzip_result:
            if pf == "windows":
                corename = Init.ftcore_name + ".exe"
            else:
                corename = Init.ftcore_name
            proxy_path = str(savepath.joinpath(corename).as_posix())
            clash_cfg = GCONFIG.config.get('clash', {})
            clash_cfg = clash_cfg if isinstance(clash_cfg, dict) else {}
            clash_cfg['path'] = proxy_path
            GCONFIG.yaml['clash'] = clash_cfg
            GCONFIG.reload()
