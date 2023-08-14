import asyncio
import importlib
import os
import re
import sys
from typing import Union, List
import socket
import yaml
from loguru import logger


class IPCleaner:
    def __init__(self, data):
        self._data = data
        self.style = config.config.get('geoip-api', 'ip-api.com')
        # logger.debug(f"当前api: {self.style}")

    def get(self, key, _default=None):
        try:
            if self._data is None:
                return {}
            return self._data[key]
        except KeyError:
            return _default
        except TypeError:
            # logger.warning("无法获取对应信息: " + str(key))
            return None

    def get_org(self):
        """
        获取组织
        :return:
        """
        if self.style == "ip.sb":
            org = self.get('asn_organization')
        elif self.style == "ip-api.com":
            org = self.get('isp')
        elif self.style == "ipleak.net":
            org = self.get('isp_name')
        elif self.style == "ipdata.co":
            org = self.get('asn', {}).get('name')
        elif self.style == "ipapi.co":
            org = self.get('org')
        else:
            org = ""
        if org:
            return org
        else:
            return ""

    def get_ip(self):
        ip = ""
        if self.style == "ip-api.com":
            ip = self.get('query')
        elif self.style == "ip.sb":
            ip = self.get('ip')
        elif self.style == "ipleak.net":
            ip = self.get('query_text')
        elif self.style == "ipdata.co":
            ip = self.get('ip')
        elif self.style == "ipapi.co":
            ip = self.get('ip')
        else:
            pass
        if ip:
            return ip
        else:
            return ""

    def get_country_code(self):
        region_code = ""
        if self.style == "ip-api.com":
            region_code = self.get('countryCode')
        elif self.style == "ip.sb":
            region_code = self.get('country_code')
        elif self.style == "ipleak.net":
            region_code = self.get('country_code')
        elif self.style == "ipdata.co":
            region_code = self.get('country_code')
        elif self.style == "ipapi.co":
            region_code = self.get('country_code')
        else:
            pass
        if region_code:
            return region_code
        else:
            return ""

    def get_city(self):
        city = ""
        if self.style == "ip-api.com":
            city = self.get('city')
        elif self.style == "ip.sb":
            city = self.get('city')
        elif self.style == "ipleak.net":
            city = self.get('city_name')
        elif self.style == "ipdata.co":
            city = self.get('city')
        elif self.style == "ipapi.co":
            city = self.get('city')
        else:
            pass
        if city:
            return city
        else:
            return ""

    def get_asn(self):
        if self.style == "ip-api.com":
            try:
                asn = self.get('as', '0').split(' ')[0]
                return asn
            except AttributeError:
                return '0'
            except IndexError:
                return '0'
        elif self.style == "ip.sb":
            asn = self.get('asn', '0')
            asd = "AS" + repr(asn)
            return asd
        elif self.style == "ipleak.net":
            asn = self.get('as_number', '0')
            asd = "AS" + repr(asn)
            return asd
        elif self.style == "ipdata.co":
            asn = self.get('asn', {}).get('asn', '0')
            return asn
        elif self.style == "ipapi.co":
            asn = self.get('asn', '0')
            return asn
        else:
            return ''


class AddonCleaner:
    """
    动态脚本导入
    """

    def __init__(self, path: str = "./addons/"):
        """
        模块管理中心
        :param path: 加载路径
        """
        self.path = path
        self._script = {}
        self.blacklist = []

    def global_test_item(self, httptest: bool = False):
        """
        经过去重并支持黑名单一并去除。最后返回一个新列表
        :return:
        """
        base_item = ['Netflix', 'Youtube', 'Disney+', 'OpenAI', 'Viu', 'steam货币', 'TVB',
                     '维基百科', '落地IP风险']
        base_item = base_item + list(self._script.keys())
        new_item = sorted(set(base_item) - set(self.blacklist), key=base_item.index)
        if httptest:
            new_item.insert(0, "HTTP(S)延迟")
        return new_item

    @property
    def script(self):
        return self._script

    def reload_script(self, blacklist: list = None, path: str = "./addons/"):
        self.init_addons(path)
        if blacklist:
            for b in blacklist:
                self._script.pop(b, None)

    def mix_script(self, alist: List[str], httptest: bool = True) -> list:
        """
        适配后端脚本不足的兼容测试项，返回后端支持的所有测试项。
        """
        newlist = list(set(alist).intersection(set(self.global_test_item())))
        newlist = sorted(newlist, key=alist.index)
        if httptest or "HTTP(S)延迟" in alist:
            newlist.insert(0, "HTTP(S)延迟")
        return newlist

    def remove_addons(self, script_name: list):
        success_list = []
        if script_name:
            for name in script_name:
                if name[-3:] == '.py' and name != "__init__.py":
                    continue
                try:
                    os.remove(self.path + name + '.py')
                    success_list.append(name)
                except FileNotFoundError as f:
                    logger.warning(f"{name} 文件不存在\t" + str(f))
                except PermissionError as p:
                    logger.warning(f"权限错误: {str(p)}")
                except Exception as e:
                    logger.error(str(e))
            return success_list
        else:
            logger.warning("script_name is empty")
            return success_list

    def init_addons(self, path: str):
        """
        动态加载测速脚本
        """
        try:
            di = os.listdir(path)
        except FileNotFoundError:
            di = None
        module_name = []
        if di is None:
            logger.warning(f"找不到 {path} 所在的路径")
        else:
            for d in di:
                if len(d) > 3:
                    if d[-3:] == '.py' and d != "__init__.py":
                        module_name.append(d[:-3])
                    else:
                        pass
        self._script.clear()
        logger.info("模块即将动态加载: " + str(module_name))
        logger.info("正在尝试获取 'SCRIPT' 属性组件")
        # module_name = ["abema"]
        num = 0
        for mname in module_name:
            try:
                mo1 = importlib.import_module(f"addons.{mname}")
            except ModuleNotFoundError as m:
                logger.warning(str(m))
                mo1 = None
            except NameError as n:
                logger.warning(str(n))
                mo1 = None
            except Exception as e:
                logger.error(str(e))
                mo1 = None
            if mo1 is None:
                continue
            try:
                script = getattr(mo1, 'SCRIPT')
            except AttributeError:
                script = None
            if script is None or type(script).__name__ != "dict":
                continue

            sname = script.get('MYNAME', None)
            stask = script.get("TASK", None)
            sget = script.get("GET", None)
            if type(stask).__name__ == 'function' and type(sname).__name__ == 'str' and type(
                    sget).__name__ == 'function':
                self._script[sname] = [stask, sget]
                num += 1
                logger.info(f"已成功加载测试脚本：{sname}")
            else:
                logger.warning("测试脚本导入格式错误")
        logger.info(f"外接测试脚本成功导入数量: {num}")

    # @staticmethod
    # def init_callback() -> list:
    #     path = os.path.join(os.getcwd(), "addons", "callback")
    #     try:
    #         di = os.listdir(path)
    #     except FileNotFoundError:
    #         di = None
    #     module_name = []
    #     callbackfunc_list = []
    #     if di is None:
    #         logger.warning(f"找不到 {path} 所在的路径")
    #     else:
    #         for d in di:
    #             if len(d) > 3:
    #                 if d.endswith('.py') and d != "__init__.py":
    #                     module_name.append(d[:-3])
    #                 else:
    #                     pass
    #     for mname in module_name:
    #         callbackfunc = None
    #         try:
    #             mo1 = importlib.import_module(f".{mname}", package="addons.callback")
    #             callbackfunc = getattr(mo1, 'callback')
    #             if callbackfunc is not None:
    #                 if asyncio.iscoroutinefunction(callbackfunc):
    #                     callbackfunc_list.append(callbackfunc)
    #         except ModuleNotFoundError as m:
    #             logger.warning(str(m))
    #         except AttributeError:
    #             pass
    #         except NameError as n:
    #             logger.warning(str(n))
    #         except Exception as e:
    #             logger.error(str(e))
    #         if callbackfunc is None:
    #             continue
    #     logger.info(f"权限回调脚本导入数量: {len(callbackfunc_list)}")
    #     return callbackfunc_list

    # def init_button(self, isreload=False):
    #     """
    #     初始化bot内联按钮
    #     """
    #     try:
    #         if isreload:
    #             self.init_addons(self.path)
    #         from pyrogram.types import InlineKeyboardButton
    #         script = addon.script
    #         button = []
    #         for k in script.keys():
    #             b = InlineKeyboardButton(f"✅{str(k)}", callback_data=f"✅{str(k)}")
    #             button.append(b)
    #         return button
    #     except Exception as e:
    #         logger.error(str(e))
    #         return []


def preTemplate():
    """
    内置模板。防止用户误删除项目文件导致出错，无法进行测试。
    """
    template_text = """
allow-lan: false
bind-address: '*'
dns:
  default-nameserver:
  - 119.29.29.29
  - 223.5.5.5
  enable: false
  enhanced-mode: fake-ip
  fallback:
  - https://208.67.222.222/dns-query
  - https://public.dns.iij.jp/dns-query
  - https://101.6.6.6:8443/dns-query
  fallback-filter:
    geoip: true
    geoip-code: CN
  listen: 0.0.0.0:53
  nameserver:
  - 119.29.29.29
  - 223.5.5.5
  - 114.114.114.114
external-controller: 127.0.0.1:11230
ipv6: true
log-level: info
mixed-port: 11220
mode: rule
proxies: null
proxy-groups:
- name: auto
  type: select
  use:
  - Default
proxy-providers:
  Default:
    health-check:
      enable: true
      interval: 600000
      url: http://www.gstatic.com/generate_204
    path: ./default.yaml
    type: file
rules:
- DOMAIN-KEYWORD,stun,auto
- DOMAIN-SUFFIX,gstatic.com,auto
- DOMAIN-KEYWORD,gstatic,auto
- DOMAIN-SUFFIX,google.com,auto
- DOMAIN-KEYWORD,google,auto
- DOMAIN,google.com,auto
- DOMAIN-SUFFIX,bilibili.com,auto
- DOMAIN-KEYWORD,bilibili,auto
- DOMAIN,bilibili.com,auto
- DOMAIN-SUFFIX,microsoft.com,auto
- DOMAIN-SUFFIX,cachefly.net,auto
- DOMAIN-SUFFIX,apple.com,auto
- DOMAIN-SUFFIX,cdn-apple.com,auto
- SRC-IP-CIDR,192.168.1.201/32,DIRECT
- IP-CIDR,127.0.0.0/8,DIRECT
- GEOIP,CN,DIRECT
- MATCH,auto
        """
    return template_text


class ClashCleaner:
    """
    yaml配置清洗
    """

    def __init__(self, _config, _config2: Union[str, bytes] = None):
        """
        :param _config: 传入一个文件对象，或者一个字符串,文件对象需指向 yaml/yml 后缀文件
        """
        self.path = ''
        self.unsupport_type = [] if config.getClashBranch() == 'meta' else ['wireguard', 'hysteria', 'tuic', 'vless']
        self.yaml = {}
        self.load(_config, _config2)
        if not isinstance(self.yaml, dict):
            self.yaml = {}

    def load(self, _config, _config2: Union[str, bytes]):
        if type(_config).__name__ == 'str':
            if _config == ':memory:':
                try:
                    if _config2 is None:
                        self.yaml = yaml.safe_load(preTemplate())
                    else:
                        self.yaml = yaml.safe_load(_config2)
                        self.check_type()
                    return
                except Exception as e:
                    logger.error(str(e))
                    self.yaml = {}
                    return
            else:
                with open(_config, 'r', encoding="UTF-8") as fp:
                    self.yaml = yaml.safe_load(fp)
                self.path = _config
        else:
            self.yaml = yaml.safe_load(_config)

    def check_type(self):
        """
        检查反序列化后的对象是否符合clash配置格式
        """
        self.check_unsupport_proxy()

    def setProxies(self, proxyinfo: list):
        """
        覆写里面的proxies键
        :return:
        """
        self.yaml['proxies'] = proxyinfo

    def check_unsupport_proxy(self):
        try:
            if self.yaml is None:
                self.yaml = {}
                return
            proxies: list = self.yaml['proxies']
            newproxies = []
            for i, proxy in enumerate(proxies):
                if isinstance(proxy, dict):
                    name = proxy['name']
                    ptype = proxy['type']
                    if not isinstance(name, str):
                        # 将节点名称转为字符串
                        proxy['name'] = str(name)
                    if ptype not in self.unsupport_type:
                        newproxies.append(proxy)
            self.yaml['proxies'] = newproxies
        except KeyError:
            logger.warning("读取节点信息失败！")
        except TypeError:
            logger.warning("读取节点信息失败！")

    def getProxies(self):
        """
        获取整个代理信息
        :return: list[dict,dict...]
        """
        try:
            return self.yaml['proxies']
        except KeyError:
            logger.warning("读取节点信息失败！")
            return []
        except TypeError:
            logger.warning("读取节点信息失败！")
            return []

    def nodesCount(self):
        """
        获取节点数量
        :return: int
        """
        try:
            return len(self.yaml['proxies'])
        except TypeError:
            logger.warning("读取节点信息失败！")
            return 0

    def nodesName(self, _filter: str = ''):
        """
        获取节点名
        :return: list
        """
        lis = []
        try:
            for i in self.yaml['proxies']:
                lis.append(str(i['name']))
            return lis
        except KeyError:
            logger.warning("读取节点信息失败！")
            return None
        except TypeError:
            logger.warning("读取节点信息失败！")
            return None

    def nodesAddr(self):
        """
        获取节点地址信息，返回（host,port）元组形式
        """
        try:
            return [(str(i['server']), i['port']) for i in self.yaml['proxies']]
        except KeyError:
            logger.warning("读取节点信息失败！")
            return None
        except TypeError:
            logger.warning("读取节点信息失败！")
            return None

    def nodesType(self):
        """
        获取节点类型
        :return: list
        """
        t = []
        try:
            for i in self.yaml['proxies']:
                t.append(str(i['type']))
            return t
        except TypeError:
            logger.warning("读取节点信息失败！")
            return None

    def nodehost(self, _filter: str = ''):
        """
        获取节点域名
        :return: list
        """
        y = []
        try:
            for i in self.yaml['proxies']:
                y.append(str(i['server']))
            return y
        except TypeError:
            logger.warning("读取节点信息失败！")
            return None

    @staticmethod
    def count_element(y: list = None):
        """
        返回入站域名信息,本质上是统计一个列表里每个元素出现的次数
        :return: dict
        """
        dip = {}
        if y is None:
            return None
        else:
            nodehosts = y
        try:
            for key in nodehosts:
                dip[key] = dip.get(key, 0) + 1
            return dip
        except Exception as e:
            logger.error(str(e))
            return None

    @staticmethod
    def count_elem(addrs: list = None):
        """
        返回入站ip信息,本质上是统计一个列表里每个元素出现的次数
        :return: dict
        """
        dic = {}
        if addrs is None:
            return None
        else:
            nodeaddrs = addrs
        try:
            for key in nodeaddrs:
                dic[key] = dic.get(key, 0) + 1
            return dic
        except Exception as e:
            logger.error(str(e))
            return None

    @logger.catch
    def proxyGroupName(self):
        """
        获取第一个"select"类型代理组的名字
        :return: str
        """
        try:
            for t in self.yaml['proxy-groups']:
                if t['type'] == 'select' and len(t['proxies']) >= self.nodesCount():
                    return t['name']
                else:
                    pass
        except TypeError:
            logger.warning("读取节点信息失败！")
            return None

    def changeClashPort(self, port: str or int = 11220):
        """
        改变配置文件端口
        """
        if 'mixed-port' in self.yaml:
            self.yaml['mixed-port'] = int(port)
            logger.info("配置端口已被改变为：" + str(port))
        elif 'port' in self.yaml:
            self.yaml['port'] = int(port)
            logger.info("配置端口已被改变为：" + str(port))

    def changeClashEC(self, ec: str = '127.0.0.1:11230'):
        """
        改变external-controller地址与端口
        """
        try:
            self.yaml['external-controller'] = ec
            logger.info("外部控制地址已被修改为：" + ec)
        except Exception as e:
            logger.error(str(e))

    def changeClashMode(self, mode: str = "global"):
        """
        改变clash模式
        """
        self.yaml['mode'] = mode
        logger.info("Clash 模式已被修改为:" + self.yaml['mode'])

    def node_filter(self, include: str = '', exclude: str = '', issave=False):
        """
        节点过滤
        :param issave: 是否保存过滤结果到文件
        :param include: 包含
        :param exclude: 排除
        :return:
        """
        logger.info(f'Node filter text>> included: {include}, excluded: {exclude}')
        result = []
        result2 = []
        nodelist = self.getProxies()
        pattern1 = pattern2 = None
        try:
            if include:
                pattern1 = re.compile(include)
            if exclude:
                pattern2 = re.compile(exclude)
        except re.error:
            logger.error("正则错误！请检查正则表达式！")
            return self.nodesName()
        except Exception as e:
            logger.error(e)
            return self.nodesName()
        if pattern1 is None:
            result = nodelist
        else:
            for node in nodelist:
                try:
                    r = pattern1.findall(node.get('name', ''))
                    if r:
                        logger.info("包含过滤器已命中:" + str(node.get('name', '')))
                        result.append(node)
                except re.error as rerror:
                    logger.error(str(rerror))
                    result.append(node)
                except Exception as e:
                    logger.error(str(e))
                    result.append(node)
        jishu1 = len(result)
        jishu2 = 0
        if pattern2 is None:
            result2 = result
        else:
            for node in result:
                try:
                    r = pattern2.findall(node.get('name', ''))
                    if r:
                        logger.info("排除过滤器已命中: " + str(node.get('name', '')))
                        jishu2 += 1
                    else:
                        result2.append(node)
                except re.error as rerror:
                    logger.error(str(rerror))
                except Exception as e:
                    logger.error(str(e))
        logger.info(f"Included {jishu1} node(s)  Excluded {jishu2} node(s)  Exported {jishu1 - jishu2} node(s)")
        self.yaml['proxies'] = result2
        if issave:
            self.save(savePath=self.path)

    @logger.catch
    def save(self, savePath: str = "./sub.yaml"):
        with open(savePath, "w", encoding="UTF-8") as fp:
            yaml.dump(self.yaml, fp)


class ConfigManager:
    """
    配置清洗，以及预处理配置在这里进行。
    """

    def __init__(self, configpath="./resources/config.yaml", data: dict = None):
        """
        configpath有一个特殊值：:memory: 将使用默认内置的模板
        还有成员变量中的 self.config 是约定为只读的
        如果要写入新值，用self.yaml代替。
        """
        self.yaml = {}
        self.config = None
        flag = 0
        if configpath == ':memory:':
            self.config = yaml.safe_load(preTemplate())
            self.yaml.update(self.config)
            return
        try:
            with open(configpath, "r", encoding="UTF-8") as fp:
                self.config = yaml.safe_load(fp)
                self.yaml.update(self.config)
        except FileNotFoundError:
            if flag == 0 and configpath == "./resources/config.yaml":
                flag += 1
                logger.warning("无法在 ./resources/ 下找到 config.yaml 配置文件，正在尝试寻找旧目录 ./config.yaml")
                try:
                    with open('./config.yaml', "r", encoding="UTF-8") as fp1:
                        self.config = yaml.load(fp1, Loader=yaml.FullLoader)
                        self.yaml.update(self.config)
                except FileNotFoundError:
                    self.config = {}
                    self.yaml = {}
            elif flag > 1:
                logger.warning("无法找到配置文件，正在初始化...")
        if self.config is None:
            di = {'loader': "Success"}
            with open(configpath, "w+", encoding="UTF-8") as fp:
                yaml.dump(di, fp)
            self.config = {}
        if data:
            with open(configpath, "w+", encoding="UTF-8") as fp:
                yaml.dump(data, fp)
            self.yaml = data

    @property
    def nospeed(self) -> bool:
        return bool(self.config.get('nospeed', False))

    def speedconfig(self):
        try:
            return self.config['speedconfig']
        except KeyError:
            return {}

    def speednodes(self):
        try:
            return self.config['speednodes']
        except KeyError:
            return int(300)

    def getClashBranch(self):
        """
        确定clash内核分支版本
        """
        branch = self.config.get('clash', {}).get('branch', 'origin')
        if branch == 'meta':
            return 'meta'
        elif isinstance(branch, str):
            return 'origin'
        else:
            raise TypeError("clash.branch配置的值不合法，请检查！")

    def getMasterconfig(self):
        return self.config.get('masterconfig', {})

    def getUserconfig(self):
        userconfig = self.config.get('userconfig', {})
        if not isinstance(userconfig, dict):
            logger.warning("userconfig的类型应为字典")
            return {}
        return userconfig

    def getSlavecomment(self, slaveid: str) -> str:
        """
        转换slaveid-->comment
        return comment
        """
        try:
            if slaveid == 'local':
                return self.get_default_slave().get('comment', 'Local')
            else:
                return self.getSlaveconfig().get(slaveid, {}).get('comment', self.getSlavecomment('local'))
        except Exception as e:
            logger.error(str(e))
            return 'Local'

    def getSlaveconfig(self):
        a = self.config.get('slaveconfig', {})
        if isinstance(a, dict):
            return a
        return {}

    def getBuildToken(self):
        token = self.config.get('buildtoken', 'c7004ded9db897e538405c67e50e0ef0c3dbad717e67a92d02f6ebcfd1022a5ad1d' +
                                '2c4419541f538ff623051759ec000d2f426e03f9709a6608570c5b9141a6b')
        if not isinstance(token, str):
            raise TypeError("buildtoken的值不合法，它应该是个字符串")
        return token

    def getBotconfig(self):
        botconfig = self.config.get('bot', {})
        if botconfig is None:
            print("bot_config为None")
            return {}
        if not botconfig:
            return botconfig
        if 'api_id' in botconfig:
            logger.info("从配置中获取到了api_id")
        if 'api_hash' in botconfig:
            logger.info("从配置中获取到了api_hash")
        if 'bot_token' in botconfig:
            logger.info("从配置中获取到了bot_token")
        return botconfig

    def getColor(self):
        return self.config.get('image', {}).get('color', {})

    def getAdmin(self) -> list:
        try:
            return self.config['admin']
        except KeyError:
            return []

    def getBridge(self):
        """
        获取连接中继桥，它是一个telegram的user_id
        """
        bridge = self.config.get('userbot', {}).get('id', None)
        return bridge

    def getGstatic(self):
        """
        获取HTTP(S)延迟测试的URL
        :return:
        """
        try:
            return self.config.get('pingurl', "http://www.gstatic.com/generate_204")
        except KeyError:
            return "http://www.gstatic.com/generate_204"

    def getuser(self):
        try:
            return self.config['user']
        except KeyError:
            logger.warning("获取用户失败,将采用默认用户")
            return []  # 默认名单

    def get_proxy_port(self):
        try:
            return self.config['proxyport']
        except KeyError:
            return None

    def get_bot_proxy(self, isjoint=True):
        """

        :param isjoint: 是否拼接代理
        :return:
        """
        try:
            if isjoint:
                return 'http://' + self.config.get('bot', {}).get('proxy', None)
            else:
                return self.config.get('bot', {}).get('proxy', None)
        except KeyError:
            return None

    def get_proxy(self, isjoint=True):
        """

        :param isjoint: 是否拼接代理
        :return:
        """
        try:
            if isjoint:
                return 'http://' + str(self.config['proxy'])
            else:
                return str(self.config['proxy'])
        except KeyError:
            return None

    def get_default_slave(self):
        return self.getSlaveconfig().get('default-slave', {})

    def get_media_item(self):
        try:
            return self.config['item']
        except KeyError:
            # logger.error("获取测试项失败，将采用默认测试项：[Netflix,Youtube,Disney,Bilibili,Dazn]")
            return ['Netflix', 'Youtube', 'Disney', 'Bilibili', 'Dazn']

    def get_clash_path(self):
        """
        clash 核心的运行路径,包括文件名
        :return: str
        """
        try:
            return self.config['clash']['path']
        except KeyError:
            logger.warning("获取运行路径失败，将采用默认运行路径: ./bin\n自动识别windows,linux,macos系统。架构默认为amd64")
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

    def get_sub(self, subname: str = None):
        """
        获取所有已保存的订阅,或者单个订阅
        :return: 单个订阅或全部订阅
        """
        if subname is None:
            try:
                return self.config['subinfo']
            except KeyError:
                logger.info("无订阅保存")
                return {}
        else:
            try:
                return self.config.get('subinfo', {}).get(subname, {})
            except KeyError:
                return {}

    @logger.catch
    def add(self, data: dict, key):
        try:
            self.yaml[key] = data[key]
        except Exception as e:
            print(e)

    @logger.catch
    def add_admin(self, admin: Union[list, str, int]):
        """
        添加管理员
        """
        adminlist = []
        if isinstance(admin, list):
            for li in admin:
                adminlist.append(li)
        else:
            adminlist.append(admin)
        try:
            old = self.config['admin']
            if old is not None:
                adminlist.extend(old)
                newadminlist = list(set(adminlist))  # 去重
                self.yaml['admin'] = newadminlist
                logger.info("添加成功")
        except KeyError:
            newadminlist = list(set(adminlist))  # 去重
            self.yaml['admin'] = newadminlist
            logger.info("添加成功")

    @logger.catch
    def del_admin(self, admin: list or str or int):
        """
        删除管理员
        """
        try:
            adminlist = self.config['admin']
            if adminlist is not None:
                if admin is list:
                    for li in admin:
                        adminlist.remove(li)
                else:
                    adminlist.remove(admin)
                self.yaml['admin'] = adminlist
        except TypeError:
            logger.error("删除失败")

    def add_slave(self, slave_id: str, key: str, username: str, comment: str = '-'):
        slaveconfig = self.config.get('slaveconfig', {})
        if slaveconfig is None:
            slaveconfig = {}
        slaveconfig[slave_id] = {'public-key': key, 'username': username, 'comment': comment}
        self.yaml['slaveconfig'] = slaveconfig

    def add_rule(self, userid: str, enable: bool = False, slaveid: str = "local", sort: str = "订阅原序",
                 script: list = None):
        """
        设定用户默认规则，后端部分
        """
        script_list = []
        if script is None:
            script_list = ['HTTP(S)延迟']
        self.get_default_slave().get('comment', 'Local')
        conf = {'enable': enable, 'slaveid': slaveid, 'sort': sort, 'script': script_list}
        uconf = self.getUserconfig()
        rconf = uconf.get('rule', {})
        rconf[userid] = conf
        self.yaml['userconfig']['rule'] = rconf
        if not self.reload():
            logger.error("重载失败")

    def add_user(self, user: list or str or int):
        """
        添加授权用户
        """
        userlist = []
        if type(user).__name__ == "list":
            for li in user:
                userlist.append(li)
        else:
            userlist.append(user)
        try:
            old = self.config['user']
            if old is not None:
                userlist.extend(old)
            newuserlist = list(set(userlist))  # 去重
            self.yaml['user'] = newuserlist
            logger.info("添加成功")
        except KeyError:
            newuserlist = list(set(userlist))  # 去重
            self.yaml['user'] = newuserlist
            logger.info("添加成功")

    @logger.catch
    def del_user(self, user: list or str or int):
        """
        删除授权用户
        """
        try:
            userlist = self.config['user']
            if userlist is not None:
                if user is list:
                    for li in user:
                        userlist.remove(li)
                else:
                    try:
                        userlist.remove(user)
                    except ValueError:
                        logger.warning("目标本身未在用户列表中")
                self.yaml['user'] = userlist
        except TypeError:
            logger.error("删除失败")

    @logger.catch
    def save(self, savePath: str = "./resources/config.yaml"):
        with open(savePath, "w+", encoding="UTF-8") as fp:
            try:
                yaml.dump(self.yaml, fp)
                return True
            except Exception as e:
                logger.error(e)
                return False

    @logger.catch
    def reload(self, configpath="./resources/config.yaml", issave=True):
        if issave:
            if self.save(savePath=configpath):
                try:
                    with open(configpath, "r", encoding="UTF-8") as fp:
                        self.config = yaml.safe_load(fp)
                        self.yaml = self.config
                        return True
                except Exception as e:
                    logger.error(e)
                    return False
        else:
            try:
                with open(configpath, "r", encoding="UTF-8") as fp:
                    self.config = yaml.safe_load(fp)
                    self.yaml = self.config
                    return True
            except Exception as e:
                logger.error(e)
                return False

    @logger.catch
    def newsub(self, subinfo: dict):
        """添加订阅"""
        try:
            self.yaml['subinfo'].update(subinfo)
        except KeyError:
            s = {'subinfo': subinfo}
            self.yaml.update(s)

    @logger.catch
    def removesub(self, subname: str):
        """
        移除订阅
        :return:
        """
        try:
            subinfo = self.yaml['subinfo']
            if subinfo is not None:
                if subname in subinfo:
                    subinfo.pop(subname)
        except KeyError:
            logger.error('移出失败')

    @logger.catch
    def delsub2provider(self, subname: str):
        try:
            subinfo = self.yaml['proxy-providers']
            if subinfo is not None:
                if subname in subinfo:
                    subinfo.pop(subname)
            subinfo2 = self.yaml['proxy-groups'][0]['use']
            if subinfo2 is not None:
                if subname in subinfo2:
                    subinfo2.remove(subname)
        except TypeError:
            logger.warning("删除失败")

    @logger.catch
    def addsub2provider(self, subname: str, subpath: str, nodefilter: str = ''):
        """
        添加订阅到总文件，如用相对路径，请注意这里的subpath是写入到配置里面的，如果你指定过clash核心的工作目录，则相对位置以clash工作目录为准
        :param nodefilter: 节点过滤
        :param subname:
        :param subpath:
        :return:
        """
        pingurl = config.getGstatic()
        info = {'type': 'file', 'path': subpath,
                'health-check': {'enable': True, 'url': pingurl, 'interval': 6000}}
        if nodefilter:
            info['filter'] = nodefilter
        self.yaml['proxy-providers'][subname] = info
        if subname not in self.yaml['proxy-groups'][0]['use']:
            self.yaml['proxy-groups'][0]['use'].append(subname)


# 内置一个配置全局变量，后续项目开发可以统一读取这个，./botmodule/init_bot.py 中也有一个
config = ConfigManager()
media_item = config.get_media_item()
addon = AddonCleaner()


def reload_config(media: list = None):
    global config, media_item
    config.reload(issave=False)
    if media is not None:
        media_item = media
    else:
        media_item = config.get_media_item()


class ReCleaner:
    """
    预测试结果清洗类
    """

    def __init__(self, data: dict, script_list: List[str] = None):
        self.data = data
        self.info = data
        self._sum = 0
        self._netflix_info = []
        self._script = addon.script
        self._script_list = media_item if script_list is None else script_list

    @property
    def script(self):
        return self._script

    def get_all(self):
        info = {}
        items = self._script_list
        try:
            for item in items:
                i = item
                if i in self.script:
                    task = self.script[i][1]
                    info[i] = task(self)
                    continue
                if i == "Youtube":
                    from addons.unlockTest import youtube
                    you = youtube.get_youtube_info(self)
                    info['Youtube'] = you
                elif i == "Disney":
                    dis = self.getDisneyinfo()
                    info['Disney'] = dis
                elif i == "Disney+":
                    dis = self.getDisneyinfo()
                    info['Disney+'] = dis
                elif i == "Dazn":
                    dazn = self.get_dazn_info()
                    info['Dazn'] = dazn
                elif i == "Netflix":
                    from addons.unlockTest import netflix
                    info['Netflix'] = netflix.get_netflix_info_new(self)
                elif i == "TVB":
                    from addons.unlockTest import tvb
                    info['TVB'] = tvb.get_TVBAnywhere_info(self)
                elif i == "Viu":
                    from addons.unlockTest import viu
                    info['Viu'] = viu.get_viu_info(self)
                elif i == "iprisk" or i == "落地IP风险":
                    from addons.unlockTest import ip_risk
                    info['落地IP风险'] = ip_risk.get_iprisk_info(self)
                elif i == "steam货币":
                    from addons.unlockTest import steam
                    info['steam货币'] = steam.get_steam_info(self)
                elif i == "维基百科":
                    from addons.unlockTest import wikipedia
                    info['维基百科'] = wikipedia.get_wikipedia_info(self)
                elif item == "OpenAI":
                    from addons.unlockTest import openai
                    info['OpenAI'] = openai.get_openai_info(self)
                else:
                    pass
        except Exception as e:
            logger.error(str(e))
        return info

    def get_https_rtt(self):
        """
        获取http(s)协议延迟
        :return: int
        """
        try:
            if 'HTTP(S)延迟' not in self.data and 'HTTPS延迟' not in self.data:
                logger.warning("采集器内无数据: HTTP(S)延迟")
                return 0
            else:
                return self.data.get('HTTP(S)延迟', 0)
        except Exception as e:
            logger.error(str(e))
            return 0

    def get_dazn_info(self):
        """
        :return: str: 解锁信息: [解锁(地区代码)、失败、N/A]
        """
        try:
            if 'dazn' not in self.data:
                logger.warning("采集器内无数据: Dazn")
                return "N/A"
            else:
                i1 = self.data.get('dazn', '')
                if i1 == '连接错误' or i1 == '超时':
                    logger.info("Dazn状态: " + i1)
                    return i1
                try:
                    info = self.data['dazn']['Region']
                    isAllowed = info['isAllowed']
                    region = info['GeolocatedCountry']
                except KeyError as k:
                    logger.error(str(k))
                    return "N/A"
                if not isAllowed:
                    logger.info("Dazn状态: " + "失败")
                    return "失败"
                elif isAllowed:
                    if region:
                        countrycode = region.upper()
                        logger.info("Dazn状态: " + "解锁({})".format(countrycode))
                        return "解锁({})".format(countrycode)
                    else:
                        logger.info("Dazn状态: " + "解锁")
                        return "解锁"
                else:
                    logger.info("Dazn状态: N/A(未找到)")
                    return "N/A"
        except Exception as e:
            logger.error(str(e))
            return "N/A"

    def getyoutubeinfo(self):
        """
        :return: str :解锁信息: (解锁、失败、N/A)
        """
        try:
            if 'youtube' not in self.data:
                logger.warning("采集器内无数据")
                return "N/A"
            else:
                text = self.data['youtube']
                if text.find('www.google.cn') != -1:
                    return "送中(CN)"
                if text.find('Premium is not available in your country') != -1 or text.find(
                        'manageSubscriptionButton') == -1:
                    return "失败"
                elif self.data['youtube_status_code'] == 200:
                    idx = text.find('"countryCode"')
                    region = text[idx:idx + 17].replace('"countryCode":"', "")
                    if idx == -1 and text.find('manageSubscriptionButton') != -1:
                        region = "US"
                    logger.info(f"Youtube解锁地区: {region}")
                    return f"解锁({region})"
                else:
                    return "未知"
        except Exception as e:
            logger.error(e)
            return "N/A"

    def getDisneyinfo(self):
        """

        :return: 解锁信息: 解锁、失败、N/A、待解
        """
        try:
            if 'disney' not in self.data:
                logger.warning("无法读取Disney Plus解锁信息")
                return "N/A"
            else:
                logger.info("Disney+ 状态：" + str(self.data['disney']))
                return self.data['disney']
        except Exception as e:
            logger.error(e)
            return "N/A"


class ResultCleaner:
    """
    测速结果的处理类，负责将得到的数据进行排序，重命名等操作
    """

    def __init__(self, info: dict):
        self.data = info

    @staticmethod
    def get_http_latency(data: list):
        """
        对所有列表延迟取平均，去除0
        :param data:
        :return:
        """
        if not data:
            raise IndexError("列表为空")
        n = len(data)
        m = len(data[0])
        new_list = []

        for j in range(m):
            col_sum = 0
            num = 0
            for i in range(n):
                if data[i][j] != 0:
                    col_sum += data[i][j]
                    num += 1
            if num:
                r1 = int(col_sum / num)
                new_list.append(r1)
            else:
                new_list.append(0)
        return new_list

    def convert_proxy_typename(self):
        if '类型' in self.data:
            new_type = []
            type1 = self.data['类型']
            if not isinstance(type1, list):
                return
            for t in type1:
                if t == 'ss':
                    new_type.append("Shadowsocks")
                elif t == "ssr":
                    new_type.append("ShadowsocksR")
                else:
                    new_type.append(t.capitalize())
            self.data['类型'] = new_type

    def start(self, sort="订阅原序"):
        try:
            self.convert_proxy_typename()
            if sort == "HTTP倒序":
                self.sort_by_ping(reverse=True)
            elif sort == "HTTP升序":
                self.sort_by_ping()
            if 'HTTP(S)延迟' in self.data:
                rtt = self.data['HTTP(S)延迟']
                new_rtt = []
                for r in rtt:
                    new_rtt.append(str(r) + 'ms')
                self.data['HTTP(S)延迟'] = new_rtt
            return self.data
        except TypeError as t:
            logger.error(str(t))
            return {}

    def sort_by_ping(self, reverse=False):
        if 'HTTP(S)延迟' not in self.data:
            return
        http_l = self.data.get('HTTP(S)延迟')
        if not reverse:
            for i in range(len(http_l)):
                if http_l[i] == 0:
                    http_l[i] = 999999
        new_list = [http_l, self.data.get('节点名称'), self.data.get('类型')]
        for k, v in self.data.items():
            if k == "HTTP(S)延迟" or k == "节点名称" or k == "类型":
                continue
            new_list.append(v)
        lists = zip(*new_list)
        lists = sorted(lists, key=lambda x: x[0], reverse=reverse)
        lists = zip(*lists)
        new_list = [list(l_) for l_ in lists]
        http_l = new_list[0] if len(new_list) > 0 else []
        if not reverse:
            for i in range(len(http_l)):
                if http_l[i] == 999999:
                    http_l[i] = 0
        if len(new_list) > 2:
            self.data['HTTP(S)延迟'] = http_l
            self.data['节点名称'] = new_list[1]
            self.data['类型'] = new_list[2]
            num = -1
            for k in self.data.keys():
                num += 1
                if k == "HTTP(S)延迟" or k == "节点名称" or k == "类型":
                    continue
                self.data[k] = new_list[num]


class ArgCleaner:
    def __init__(self, string: str = None):
        self.string = string

    @staticmethod
    def getarg(string: str, sep: str = ' ') -> list[str]:
        """
        对字符串使用特定字符进行切片
        Args:
            string: 要切片的字符串
            sep: 指定用来切片的字符依据，默认为空格

        Returns: 返回一个切好的字符串列表

        """
        return [x for x in string.strip().split(sep) if x != ''] if string is not None else []

    def getall(self, string: str = None):
        """
        分割一段字符串中的参数，返回参数列表
        """
        if string is None:
            if self.string is None:
                return None
            arg = self.string.strip().split(' ')
            arg = [x for x in arg if x != '']
            return arg
        else:
            arg = string.strip().split(' ')
            arg = [x for x in arg if x != '']
            return arg


def geturl(string: str):
    text = string
    pattern = re.compile(
        r"https?://(?:[a-zA-Z]|\d|[$-_@.&+]|[!*,]|[\w\u4e00-\u9fa5])+")  # 匹配订阅地址
    # 获取订阅地址
    try:
        url = pattern.findall(text)[0]  # 列表中第一个项为订阅地址
        return url
    except IndexError:
        return None


@logger.catch
def domain_to_ip(host: str):
    """
    将域名转成IPv4和IPv6地址
    :param host:
    :return: 返回IP地址列表,如果无法解析返回None
    """
    try:
        results = socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        ips = set()
        for result in results:
            ips.add(result[4][0])
        ip = list(ips)
        return ip
    except socket.gaierror:
        return None


def cluster(host):
    cluip = domain_to_ip(host)
    if cluip is None:
        return None
    else:
        clus = len(cluip)
        return clus


def count(host):
    ips = domain_to_ip(host)
    if ips is None:
        return None

    ipv4_count = 0
    ipv6_count = 0

    for ip in ips:
        if ":" in ip:
            ipv6_count += 1
        else:
            ipv4_count += 1

    if ipv4_count > 0 and ipv6_count == 0:
        return "4"
    elif ipv6_count > 0 and ipv4_count == 0:
        return "6"
    elif ipv4_count > 0 and ipv6_count > 0:
        return "46"
    else:
        return None


def batch_ipstack(host: list):
    """
    批量将域名转成栈列表
    :param host: 一个列表
    :return:
    """
    ipstack = []
    for h in host:
        if type(h).__name__ == 'dict':
            try:
                ipss = count(h['ipstart'])
                if ipss:
                    h['ipstart'] = ipss
                else:
                    h['ipstart'] = "N/A"
                ipstack.append(h)
            except KeyError:
                h['ipstart'] = "N/A"
                ipstack.append(h)
        else:
            ipss = count(h)
            if ipss:
                ipstack.append(ipss)
            else:
                ipstack.append("N/A")
    return ipstack


def batch_domain2ip(host: list):
    """
    批量将域名转成ip地址
    :param host: 一个列表
    :return:
    """
    ipaddrs = []
    for h in host:
        if type(h).__name__ == 'dict':
            try:
                ips = domain_to_ip(h['server'])
                if ips:
                    h['server'] = ips[0]
                else:
                    h['server'] = "N/A"
                ipaddrs.append(h)
            except KeyError:
                h['server'] = "N/A"
                ipaddrs.append(h)
        else:
            ips = domain_to_ip(h)
            if ips:
                ipaddrs.append(ips[0])
            else:
                ipaddrs.append("N/A")
    return ipaddrs


def batch_ipcu(host: list):
    """
    批量将域名转成簇列表
    :param host: 一个列表
    :return:
    """
    ipcu = []
    for h in host:
        if type(h).__name__ == 'dict':
            try:
                ipss = cluster(h['ipcu'])
                if ipss:
                    h['ipcu'] = ipss
                else:
                    h['ipcu'] = "N/A"
                ipcu.append(h)
            except KeyError:
                h['ipcu'] = "N/A"
                ipcu.append(h)
        else:
            ipss = cluster(h)
            if ipss:
                ipcu.append(ipss)
            else:
                ipcu.append("N/A")
    return ipcu
