# 这是一个批量启动clash子进程的脚本
import asyncio
import subprocess
import sys
import time
import yaml
from time import sleep


class ClashCleaner:
    """
    yaml配置清洗
    """

    def __init__(self, _config):
        """
        :param _config: 传入一个文件对象，或者一个字符串,文件对象需指向 yaml/yml 后缀文件
        """
        if type(_config).__name__ == 'str':
            with open(_config, 'r', encoding="UTF-8") as fp:
                self.yaml = yaml.safe_load(fp)
        else:
            self.yaml = yaml.safe_load(_config)

    def changeClashPort(self, port: str or int = 11220):
        """
        改变配置文件端口
        """
        if 'mixed-port' in self.yaml:
            self.yaml['mixed-port'] = int(port)
            print("配置端口已被改变为：" + str(port))
        elif 'port' in self.yaml:
            self.yaml['port'] = int(port)
            print("配置端口已被改变为：" + str(port))

    def changeClashEC(self, ec: str = '127.0.0.1:11230'):
        """
        改变external-controller地址与端口
        """
        try:
            self.yaml['external-controller'] = ec
            print("外部控制地址已被修改为：" + ec)
        except Exception as e:
            print(str(e))

    def save(self, savePath: str = "./sub.yaml"):
        with open(savePath, "w", encoding="UTF-8") as fp:
            yaml.dump(self.yaml, fp)


class ConfigManager:
    """
    配置清洗
    """

    def __init__(self, configpath="./resources/config.yaml", data: dict = None):
        """

        """
        self.yaml = {}
        self.config = None
        flag = 0
        try:
            with open(configpath, "r", encoding="UTF-8") as fp:
                self.config = yaml.safe_load(fp)
                self.yaml.update(self.config)
        except FileNotFoundError:
            if flag == 0 and configpath == "./resources/config.yaml":
                flag += 1
                print("无法在 ./resources/ 下找到 config.yaml 配置文件，正在尝试寻找旧目录 ./config.yaml")
                with open('./config.yaml', "r", encoding="UTF-8") as fp1:
                    self.config = yaml.safe_load(fp1)
                    self.yaml.update(self.config)
            elif flag > 1:
                print("无法找到配置文件，正在初始化...")
        if self.config is None:
            di = {'loader': "Success"}
            with open(configpath, "w+", encoding="UTF-8") as fp:
                yaml.dump(di, fp)
            self.config = {}
        if data:
            with open(configpath, "w+", encoding="UTF-8") as fp:
                yaml.dump(data, fp)
            self.yaml = data

    def get_clash_work_path(self):
        """
        clash工作路径
        :return:
        """
        try:
            return self.config['clash']['workpath']
        except KeyError:
            print("获取工作路径失败，将采用默认工作路径 ./clash")
            try:
                d = {'workpath': './clash'}
                self.yaml['clash'].update(d)
            except KeyError:
                di = {'clash': {'workpath': './clash'}}
                self.yaml.update(di)
            return './clash'

    def get_clash_path(self):
        """
        clash 核心的运行路径,包括文件名
        :return: str
        """
        try:
            return self.config['clash']['path']
        except KeyError:
            if sys.platform.startswith("linux"):
                path = './bin/fulltclash-linux-amd64'
            elif sys.platform.startswith("win32"):
                path = r'.\bin\fulltclash-windows-amd64.exe'
            elif 'darwin' in sys.platform:
                path = './bin/fulltclash-macos-amd64'
            else:
                path = './bin/fulltclash-linux-amd64'
            d = {'path': path}
            try:
                self.yaml['clash'].update(d)
            except KeyError:
                di = {'clash': d}
                self.yaml.update(di)
            return path


config = ConfigManager()


async def is_port_in_use(host='127.0.0.1', port=80):
    """
    检查主机端口是否被占用
    :param host:
    :param port:
    :return:
    """
    try:
        _, writer = await asyncio.open_connection(host, port)
        writer.close()
        await writer.wait_closed()
        # print(fr"{port} 端口已被占用，请更换。")
        return True
    except ConnectionRefusedError:
        return False


async def check_port(start: int, end: int):
    tasks = []
    for i in range(start, end):
        tasks.append(asyncio.create_task(is_port_in_use(port=i)))
    results = await asyncio.gather(*tasks)
    return True in results


# def start_client(path: str, workpath: str = "./clash", _config: str = './clash/proxy.yaml', ):
#     # 启动了一个clash常驻进程
#     # _command = fr"{path} -f {_config} -d {workpath}"
#     # subprocess.Popen(_command.split(), encoding="utf-8")
#     sleep(2)


# def new_batch_start(portlist: list):
#     from utils.proxys import lib, Clash
#     _myclash = getattr(lib, 'myclash')
#     _myclash.argtypes = [ctypes.c_char_p, ctypes.c_longlong]
#     # create a task for myclash
#     addr = ["127.0.0.1:" + str(p) for p in portlist]
#     for _i in range(len(addr)):
#         clash = Clash(portlist[_i], _i)
#         clash.daemon = True
#         clash.start()


def start_fulltclash(portlist: list):
    if not portlist:
        raise ValueError("空的端口列表")
    port2 = "|".join(portlist)
    control_port = int(portlist[0])-1
    _command = fr"{config.get_clash_path()} -c {control_port} -p {port2}"
    p = subprocess.Popen(_command.split(), encoding="utf-8")
    return p


# def batch_start(portlist: list, proxy_file_path="./clash/proxy.yaml"):
#     """
#     批量启动多个clash进程
#     :param proxy_file_path: 代理配置文件路径
#     :param portlist: 端口列表，请至少间隔一个数字，如[1124,1126,1128,...]
#     :return:
#     """
#
#     ecport = [i + 1 for i in portlist]
#     if len(list(set(portlist).intersection(set(ecport)))):
#         print("代理端口组请至少间隔一个数字，如[1124,1126,1128,...]")
#         raise ValueError("代理端口组请至少间隔一个数字，如[1124,1126,1128,...]")
#     for i in range(len(portlist)):
#         clashconf = ClashCleaner(proxy_file_path)
#         clashconf.changeClashPort(port=portlist[i])
#         clashconf.changeClashEC(ec="127.0.0.1:" + str(ecport[i]))
#         clashconf.save(proxy_file_path)
#         start_client(path=config.get_clash_path(), workpath=config.get_clash_work_path(), _config=proxy_file_path)
#     clashconf = ClashCleaner(proxy_file_path)
#     clashconf.changeClashPort(port=11220)
#     clashconf.changeClashEC(ec="127.0.0.1:11230")
#     clashconf.save(proxy_file_path)

if __name__ == "__main__":
    clash_path = config.get_clash_path()  # 为clash核心运行路径, Windows系统需要加后缀名.exe
    clash_work_path = config.get_clash_work_path()  # clash工作路径
    corenum = config.config.get('clash', {}).get('core', 1)
    start_port = config.config.get('clash', {}).get('startup', 11220)
    res1 = asyncio.run(check_port(11220, 11230))
    res2 = asyncio.run(check_port(start_port, start_port + 1 + corenum * 2))
    if res1 or res2:
        print("端口检查中发现已有其他进程占用了端口，如果您已单独运行clash启动器，请忽略这条提示")
        sleep(5)
        exit(1)
    # command = fr"{clash_path} -f {'./clash/proxy.yaml'} -d {clash_work_path}"
    # subp = subprocess.Popen(command.split(), encoding="utf-8")

    sleep(1)
    # new_batch_start([start_port + i * 2 for i in range(corenum)])
    start_fulltclash([start_port + i * 2 for i in range(corenum)])
    # batch_start([start_port + i * 2 for i in range(corenum)])
    print("Clash核心进程已启动!")
    try:
        # subp.wait()
        import signal

        signal.signal(signal.SIGINT, signal.SIG_DFL)
    except KeyboardInterrupt:
        exit()
