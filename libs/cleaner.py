import importlib
import os
import re
import socket
import yaml
from loguru import logger


class IPCleaner:
    def __init__(self, data):
        self._data = data
        self.style = config.config.get('geoip-api', 'ip-api.com')

    def get(self, key, _default=None):
        try:
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
        self.init_addons(path)
        self.blacklist = []

    def global_test_item(self):
        base_item = ['Netflix', 'Youtube', 'Disney+', 'Primevideo', 'Viu', 'steam货币', 'OpenAI',
                     '维基百科', '落地IP风险']
        test_item = set(list(self._script.keys()) + base_item)
        new_item = test_item - set(self.blacklist)
        return list(new_item)

    @property
    def script(self):
        return self._script

    def reload_script(self, blacklist: list = None, path: str = "./addons/"):
        self.init_addons(path)
        if blacklist:
            for b in blacklist:
                self._script.pop(b, None)

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
                    logger.warning(f"{name} 文件不存在\t"+str(f))
                except PermissionError as p:
                    logger.warning(f"权限错误: {str(p)}")
                except Exception as e:
                    logger.error(str(e))
            return success_list
        else:
            logger.warning("script_name is empty")
            return success_list

    def init_addons(self, path: str):
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
            except AttributeError as a:
                logger.warning(str(a))
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

    @staticmethod
    def init_button():
        try:
            from pyrogram.types import InlineKeyboardButton
            script = addon.script
            button = []
            for k in script.keys():
                b = InlineKeyboardButton(f"✅{str(k)}", callback_data=f"✅{str(k)}")
                button.append(b)
            return button
        except Exception as e:
            logger.error(str(e))
            return []


class ClashCleaner:
    """
    yaml配置清洗
    """

    def __init__(self, _config):
        """
        :param _config: 传入一个文件对象，或者一个字符串,文件对象需指向 yaml/yml 后缀文件
        """
        self.path = ''
        self.yaml = {}
        if type(_config).__name__ == 'str':
            with open(_config, 'r', encoding="UTF-8") as fp:
                self.yaml = yaml.load(fp, Loader=yaml.FullLoader)
            self.path = _config
        else:
            self.yaml = yaml.load(_config, Loader=yaml.FullLoader)

    def getProxies(self):
        """
        获取整个代理信息
        :return: list[dict,dict...]
        """
        try:
            return self.yaml['proxies']
        except KeyError:
            logger.warning("读取节点信息失败！")
            return None
        except TypeError:
            logger.warning("读取节点信息失败！")
            return None

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
                lis.append(i['name'])
            return lis
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
                t.append(i['type'])
            return t
        except TypeError:
            logger.warning("读取节点信息失败！")
            return None

    def nodesAddr(self, name=None):
        """
        获取节点地址
        :return: list | str
        """
        if name:
            try:
                for i in self.yaml['proxies']:
                    if name == i['name']:
                        return i['server']
                    else:
                        pass
                return None
            except TypeError:
                logger.warning("读取节点信息失败")
                return None
            except KeyError:
                logger.warning("读取节点信息失败！")
                return None
        addrs = []
        try:
            for i in self.yaml['proxies']:
                addrs.append(i['server'])
            return addrs
        except TypeError:
            logger.warning("读取节点信息失败")
            return None
        except KeyError:
            logger.warning("读取节点信息失败！")
            return None

    @staticmethod
    def count_element(addrs: list = None):
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

    def changeClashPort(self, port: str or int = 1122):
        """
        改变配置文件端口
        """
        if 'mixed-port' in self.yaml:
            self.yaml['mixed-port'] = int(port)
            logger.info("配置端口已被改变为：" + str(port))
        elif 'port' in self.yaml:
            self.yaml['port'] = int(port)
            logger.info("配置端口已被改变为：" + str(port))

    def changeClashEC(self, ec: str = '127.0.0.1:1123'):
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

    def node_filter(self, include: str = '', exclude: str = ''):
        """
        节点过滤
        :param include: 包含
        :param exclude: 排除
        :return:
        """
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
        self.save(savePath=self.path)

    @logger.catch
    def save(self, savePath: str = "./sub.yaml"):
        with open(savePath, "w", encoding="UTF-8") as fp:
            yaml.dump(self.yaml, fp)


@logger.catch()
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

    def getFont(self):
        return self.config.get('font', "./resources/阿里巴巴普惠体-Regular.ttf")

    def getColor(self):
        return self.config.get('image', {}).get('color', {})

    def getAdmin(self) -> list:
        try:
            return self.config['admin']
        except KeyError:
            return []

    def getGstatic(self):
        """
        获取HTTP延迟测试的URL
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

    def get_media_item(self):
        try:
            return self.config['item']
        except KeyError:
            # logger.error("获取测试项失败，将采用默认测试项：[Netflix,Youtube,Disney,Bilibili,Dazn]")
            return ['Netflix', 'Youtube', 'Disney', 'Bilibili', 'Dazn']

    def get_clash_work_path(self):
        """
        clash工作路径
        :return:
        """
        try:
            return self.config['clash']['workpath']
        except KeyError:
            logger.warning("获取工作路径失败，将采用默认工作路径 ./clash")
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
            logger.warning("获取运行路径失败，将采用默认运行路径 ./resources/clash-windows-amd64.exe")
            try:
                d = {'path': './resources/clash-windows-amd64.exe'}
                self.yaml['clash'].update(d)
            except KeyError:
                di = {'clash': {'path': './resources/clash-windows-amd64.exe'}}
                self.yaml.update(di)
            return './resources/clash-windows-amd64.exe'

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
    def add_admin(self, admin: list or str or int):
        """
        添加管理员
        """
        adminlist = []

        if admin is list:
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

    @logger.catch
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
                        self.config = yaml.load(fp, Loader=yaml.FullLoader)
                        self.yaml = self.config
                        return True
                except Exception as e:
                    logger.error(e)
                    return False
        else:
            try:
                with open(configpath, "r", encoding="UTF-8") as fp:
                    self.config = yaml.load(fp, Loader=yaml.FullLoader)
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
    def __init__(self, data: dict):
        self.data = data
        self._sum = 0
        self._netflix_info = []
        self._script = addon.script

    @property
    def script(self):
        return self._script

    def get_all(self):
        info = {}
        items = media_item
        try:
            for item in items:
                i = item
                if i in self.script:
                    task = self.script[i][1]
                    info[i] = task(self)
                    continue
                if i == "Youtube":
                    you = self.getyoutubeinfo()
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
                elif i == "Primevideo":
                    from addons.unlockTest import primevideo
                    info['Primevideo'] = primevideo.get_primevideo_info(self)
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
            if 'HTTP延迟' not in self.data and 'HTTPS延迟' not in self.data:
                logger.warning("采集器内无数据: HTTP延迟")
                return 0
            else:
                return self.data.get('HTTP延迟', 0)
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
                if text.find('Premium is not available in your country') != -1 or text.find(
                        'manageSubscriptionButton') == -1:
                    return "失败"
                if text.find('www.google.cn') != -1:
                    return "送中(CN)"
                elif self.data['youtube_status_code'] == 200:
                    idx = text.find('"countryCode"')
                    region = text[idx:idx + 17].replace('"countryCode":"', "")
                    if idx == -1 and text.find('manageSubscriptionButton') != -1:
                        region = "US"
                    logger.info(f"Youtube解锁地区: {region}")
                    return f"解锁({region})"
                else:
                    return "N/A"
        except Exception as e:
            logger.error(e)
            return "N/A"

    def getDisneyinfo(self):
        """

        :return: 解锁信息: 解锁、失败、N/A、待解
        """
        try:
            if 'disney' not in self.data:
                logger.warning("无法读取Desney Plus解锁信息")
                return "N/A"
            else:
                logger.info("Disney+ 状态：" + str(self.data['disney']))
                return self.data['disney']
        except Exception as e:
            logger.error(e)
            return "N/A"


class ResultCleaner:
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

    def start(self, sort="订阅原序"):
        try:
            if '类型' in self.data:
                type1 = self.data['类型']
                new_type = []
                for t in type1:
                    if t == 'ss':
                        new_type.append("Shadowsocks")
                    elif t == "ssr":
                        new_type.append("ShadowsocksR")
                    else:
                        new_type.append(t.capitalize())
                self.data['类型'] = new_type
            if sort == "HTTP倒序":
                self.sort_by_ping(reverse=True)
            elif sort == "HTTP升序":
                self.sort_by_ping()
            if 'HTTP延迟(内核)' in self.data:
                rtt = self.data['HTTP延迟(内核)']
                new_rtt = []
                for r in rtt:
                    new_rtt.append(str(r) + 'ms')
                self.data['HTTP延迟(内核)'] = new_rtt
            if 'HTTP延迟' in self.data:
                rtt = self.data['HTTP延迟']
                new_rtt = []
                for r in rtt:
                    new_rtt.append(str(r) + 'ms')
                self.data['HTTP延迟'] = new_rtt
            return self.data
        except TypeError:
            return {}

    def sort_by_ping(self, reverse=False):
        http_l = self.data.get('HTTP延迟')
        if not reverse:
            for i in range(len(http_l)):
                if http_l[i] == 0:
                    http_l[i] = 999999
        new_list = [http_l, self.data.get('节点名称'), self.data.get('类型')]
        for k, v in self.data.items():
            if k == "HTTP延迟" or k == "节点名称" or k == "类型":
                continue
            new_list.append(v)
        lists = zip(*new_list)
        lists = sorted(lists, key=lambda x: x[0], reverse=reverse)
        lists = zip(*lists)
        new_list = [list(l_) for l_ in lists]
        http_l = new_list[0]
        if not reverse:
            for i in range(len(http_l)):
                if http_l[i] == 999999:
                    http_l[i] = 0
        if len(new_list) > 2:
            self.data['HTTP延迟'] = http_l
            self.data['节点名称'] = new_list[1]
            self.data['类型'] = new_list[2]
            num = -1
            for k in self.data.keys():
                num += 1
                if k == "HTTP延迟" or k == "节点名称" or k == "类型":
                    continue
                self.data[k] = new_list[num]


class ArgCleaner:
    def __init__(self, string: str = None):
        self.string = string

    def getall(self, string: str = None):
        if string is None:
            if self.string is None:
                return None
            arg = self.string.strip().split(' ')
            c = 0
            while len(arg) > c:
                if arg[c] == '':
                    del arg[c]
                else:
                    c += 1
            return arg
        else:
            arg = string.strip().split(' ')
            c = 0
            while len(arg) > c:
                if arg[c] == '':
                    del arg[c]
                else:
                    c += 1
            return arg


def geturl(string: str):
    text = string
    pattern = re.compile(
        r"https?://(?:[a-zA-Z]|\d|[$-_@.&+]|[!*,]|(?:%[\da-fA-F][\da-fA-F])|[\w\u4e00-\u9fa5])+")  # 匹配订阅地址
    # 获取订阅地址
    try:
        url = pattern.findall(text)[0]  # 列表中第一个项为订阅地址
        return url
    except IndexError:
        print("未找到URL")
        return None


def replace(arg, old, new):
    """
    将arg里的某个值替换成新的值
    :param arg: 传入的对象
    :param old: 旧值
    :param new: 新值
    :return: 新的对象
    """
    if type(arg).__name__ == 'list':
        new_arg = []
        for a in arg:
            if a == old:
                logger.info("替换了一个值: {}-->{}".format(a, new))
                new_arg.append(new)
            else:
                new_arg.append(a)
        return new_arg
    elif type(arg).__name__ == 'tuple':
        new_arg = ()
        for a in arg:
            if a == old:
                new_arg += (new,)
            else:
                new_arg += (a,)
        return new_arg
    elif type(arg).__name__ == 'str':
        # 我觉得这个if分支挺废的，但我还是留了下来，给后人当个乐子。
        if arg == old:
            return str(new)
        else:
            return arg
    else:
        print("无可替换内容")
        return arg


@logger.catch
def domain_to_ip(host: str):
    """
    将域名转成ip
    :param host:
    :return:
    """
    try:
        ip = socket.gethostbyname(host)
        return ip
    except socket.gaierror:
        return None


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
                ip = domain_to_ip(h['server'])
                if ip:
                    h['server'] = ip
                else:
                    h['server'] = "N/A"
                ipaddrs.append(h)
            except KeyError:
                h['server'] = "N/A"
                ipaddrs.append(h)
        else:
            ip = domain_to_ip(h)
            if ip:
                ipaddrs.append(ip)
            else:
                ipaddrs.append("N/A")
    return ipaddrs


def get_airport_info(text: str = None):
    """
    过去特定格式的信息
    :return:
    """
    jcid = jcname = jctime = jcurl = jcgroup = jccomment = jcchannel = jcowner = ''
    try:
        a = text if text is not None else ''
        b = a.split('\n')
        p1 = re.search('[序编]?号[:：]?.*(\d)+', a)
        if p1 is not None:
            jcid = p1.group()
        b.pop(0)
        prename = b.pop(0) if len(b) else ''
        names = prename.split(' ')
        for n in names:
            if n:
                if n[0] == '#':
                    jcname += n[1:] + ' '
                else:
                    jcname += n + ' '
        prename = re.search("名称[:：]?.*", a)
        if prename is not None:
            jcname = prename.group()[3:]
        timepattern = re.compile(r"时间[:：].?(\d+\W\d+\W\d+)")
        pretime = timepattern.search(a)
        if pretime is not None:
            jctime = pretime.group()[3:]
        preurl = re.search("官网[:：].*", a)
        if preurl is not None:
            jcurl = preurl.group()[3:]
        pretgg1 = re.search("群组[:：].*@\w+", a)
        if pretgg1 is not None:
            jcgroup = pretgg1.group()[3:]
        else:
            pretgg2 = re.search("群组[:：].*", a)
            if pretgg2 is not None:
                jcgroup = pretgg2.group()[3:]
        pretgc1 = re.search("频道[:：].*@\w+", a)
        if pretgc1 is not None:
            jcchannel = pretgc1.group()[3:]
        else:
            pretgc2 = re.search("频道[:：].*", a)
            if pretgc2 is not None:
                jcchannel = pretgc2.group()[3:]
        commentp = re.compile("[说明|简要介绍|备注][:：]?.*")
        pre_comment = commentp.search(a)
        if pre_comment is not None:
            t = pre_comment.group()
            index1 = t.find(':')
            index2 = t.find('：')
            if index1 > 0:
                jccomment = t[index1 + 1:]
            elif index2 > 0:
                jccomment = t[index2 + 1:]
        # print(jcid)
        # print(jcname)
        # print(jctime)
        # print(jcurl)
        # print(jcgroup)
        # print(jcchannel)
        # print(jccomment)
        return jcid, jcname, jctime, jcurl, jcgroup, jcchannel, jccomment, jcowner
    except Exception as e:
        logger.error(str(e))
        return jcid, jcname, jctime, jcurl, jcgroup, jcchannel, jccomment, jcowner
