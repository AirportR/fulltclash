# 这是一个批量启动clash子进程的脚本
import asyncio
import subprocess
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
                self.yaml = yaml.load(fp, Loader=yaml.FullLoader)
        else:
            self.yaml = yaml.load(_config, Loader=yaml.FullLoader)

    def changeClashPort(self, port: str or int = 1122):
        """
        改变配置文件端口
        """
        if 'mixed-port' in self.yaml:
            self.yaml['mixed-port'] = int(port)
            print("配置端口已被改变为：" + str(port))
        elif 'port' in self.yaml:
            self.yaml['port'] = int(port)
            print("配置端口已被改变为：" + str(port))

    def changeClashEC(self, ec: str = '127.0.0.1:1123'):
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
                self.config = yaml.load(fp, Loader=yaml.FullLoader)
                self.yaml.update(self.config)
        except FileNotFoundError:
            if flag == 0 and configpath == "./resources/config.yaml":
                flag += 1
                print("无法在 ./resources/ 下找到 config.yaml 配置文件，正在尝试寻找旧目录 ./config.yaml")
                with open('./config.yaml', "r", encoding="UTF-8") as fp1:
                    self.config = yaml.load(fp1, Loader=yaml.FullLoader)
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
            print("获取运行路径失败，将采用默认运行路径 ./resources/clash-windows-amd64.exe")
            try:
                d = {'path': './resources/clash-windows-amd64.exe'}
                self.yaml['clash'].update(d)
            except KeyError:
                di = {'clash': {'path': './resources/clash-windows-amd64.exe'}}
                self.yaml.update(di)
            return './resources/clash-windows-amd64.exe'


async def is_port_in_use(host='127.0.0.1', port=80):
    """
    检查主机端口是否被占用
    :param host:
    :param port:
    :return:
    """
    try:
        reader, writer = await asyncio.open_connection(host, port)
        writer.close()
        await writer.wait_closed()
        print(fr"{port} 端口已被占用，请更换。")
        return True
    except ConnectionRefusedError:
        return False


async def check_port(start: int, end: int):
    tasks = []
    for i in range(start, end):
        tasks.append(asyncio.create_task(is_port_in_use(port=i)))
    results = await asyncio.gather(*tasks)
    return True in results


def start_client(path: str, workpath: str = "./clash", _config: str = './clash/proxy.yaml', ):
    # 启动了一个clash常驻进程
    _command = fr"{path} -f {_config} -d {workpath}"
    subprocess.Popen(_command.split(), encoding="utf-8")
    sleep(2)


def batch_start(portlist: list, proxy_file_path="./clash/proxy.yaml"):
    """
    批量启动多个clash进程
    :param proxy_file_path: 代理配置文件路径
    :param portlist: 端口列表，请至少间隔一个数字，如[1124,1126,1128,...]
    :return:
    """

    ecport = [i + 1 for i in portlist]
    if len(list(set(portlist).intersection(set(ecport)))):
        print("代理端口组请至少间隔一个数字，如[1124,1126,1128,...]")
        raise ValueError("代理端口组请至少间隔一个数字，如[1124,1126,1128,...]")
    for i in range(len(portlist)):
        clashconf = ClashCleaner(proxy_file_path)
        clashconf.changeClashPort(port=portlist[i])
        clashconf.changeClashEC(ec="127.0.0.1:" + str(ecport[i]))
        clashconf.save(proxy_file_path)
        start_client(path=config.get_clash_path(), workpath=config.get_clash_work_path(), _config=proxy_file_path)
    clashconf = ClashCleaner(proxy_file_path)
    clashconf.changeClashPort(port=1122)
    clashconf.changeClashEC(ec="127.0.0.1:1123")
    clashconf.save(proxy_file_path)


if __name__ == "__main__":
    config = ConfigManager()
    clash_path = config.get_clash_path()  # 为clash核心运行路径, Windows系统需要加后缀名.exe
    clash_work_path = config.get_clash_work_path()  # clash工作路径
    corenum = config.config.get('clash', {}).get('core', 1)
    res = asyncio.run(check_port(1122, 1123 + corenum * 2))
    if res:
        print("端口检查未通过，即将退出...")
        sleep(10)
        exit(1)
    command = fr"{clash_path} -f {'./clash/proxy.yaml'} -d {clash_work_path}"
    subp = subprocess.Popen(command.split(), encoding="utf-8")

    sleep(2)
    batch_start([1124 + i * 2 for i in range(corenum)])
    print("Clash核心进程已启动!")
    try:
        subp.wait()
    except KeyboardInterrupt:
        exit()
