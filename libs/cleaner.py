import re
import socket
import yaml
from bs4 import BeautifulSoup
from loguru import logger


class IPCleaner:
    def __init__(self, data):
        self._data = data
        self.style = config.config.get('geoip-api', 'ip-api.com')

    def get(self, key):
        try:
            return self._data[key]
        except KeyError as k:
            logger.error(str(k))
            return None
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
        asn = ""
        try:
            if self.style == "ip-api.com":
                asn = self.get('as').split(' ')[0]
            elif self.style == "ip.sb":
                asn = self.get('asn')
            else:
                pass
            if asn:
                return asn
            else:
                return "0"
        except Exception as e:
            # logger.warning(str(e))
            return "0"


class ClashCleaner:
    """
    yaml配置清洗
    """

    def __init__(self, config):
        """
        :param config: 传入一个文件对象，或者一个字符串,文件对象需指向 yaml/yml 后缀文件
        """
        if type(config).__name__ == 'str':
            with open(config, 'r', encoding="UTF-8") as fp:
                self.yaml = yaml.load(fp, Loader=yaml.FullLoader)
        else:
            self.yaml = yaml.load(config, Loader=yaml.FullLoader)

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

    def nodesName(self):
        """
        获取节点名
        :return: list
        """
        lis = []
        try:
            for i in self.yaml['proxies']:
                lis.append(i['name'])
            return lis
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
                with open('./config.yaml', "r", encoding="UTF-8") as fp1:
                    self.config = yaml.load(fp1, Loader=yaml.FullLoader)
                    self.yaml.update(self.config)
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

    def getFont(self):
        return self.config.get('font', "./resources/苹方黑体-准-简.ttf")

    def getColor(self):
        return self.config.get('color', {})

    def getAdmin(self) -> list:
        try:
            return self.config['admin']
        except KeyError:
            return []

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
        :return:
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
    def delsub(self, subname: str):
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
    def addsub(self, subname: str, subpath: str):
        """
        添加订阅到总文件，如用相对路径，请注意这里的subpath是写入到配置里面的，如果你指定过clash核心的工作目录，则相对位置以clash工作目录为准
        :param subname:
        :param subpath:
        :return:
        """
        info = {'type': 'file', 'path': subpath,
                'health-check': {'enable': True, 'url': 'http://www.gstatic.com/generate_204', 'interval': 600}}
        self.yaml['proxy-providers'][subname] = info
        if subname not in self.yaml['proxy-groups'][0]['use']:
            self.yaml['proxy-groups'][0]['use'].append(subname)


config = ConfigManager()
media_item = config.get_media_item()


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

    def get_all(self):
        info = {}
        items = media_item
        try:
            for item in items:
                i = item.capitalize()
                # if i == "Netflix":
                #     nf = self.getnetflixinfo()
                #     info['Netflix'] = nf[len(nf) - 1] #旧奈飞测试，已废弃
                if i == "Youtube":
                    you = self.getyoutubeinfo()
                    info['Youtube'] = you
                elif i == "Disney":
                    dis = self.getDisneyinfo()
                    info['Disney'] = dis
                elif i == "Disney+":
                    dis = self.getDisneyinfo()
                    info['Disney+'] = dis
                elif i == "Bilibili":
                    bili = self.get_bilibili_info()
                    info['Bilibili'] = bili
                elif i == "Dazn":
                    dazn = self.get_dazn_info()
                    info['Dazn'] = dazn
                elif i == "Hbomax":
                    from addons.unlockTest import hbomax
                    hbomaxinfo = hbomax.get_hbomax_info(self)
                    info['Hbomax'] = hbomaxinfo
                elif i == "Bahamut":
                    from addons.unlockTest import bahamut
                    info['Bahamut'] = bahamut.get_bahamut_info(self)
                elif i == "Netflix":
                    from addons.unlockTest import netflix
                    info['Netflix'] = netflix.get_netflix_info_new(self)
                elif i == "Abema":
                    from addons.unlockTest import abema
                    info['Abema'] = abema.get_abema_info(self)
                elif i == "Bbc":
                    from addons.unlockTest import bbciplayer
                    info['BBC'] = bbciplayer.get_bbc_info(self)
                elif i == "公主链接":
                    from addons.unlockTest import pcrjp
                    info['公主链接'] = pcrjp.get_pcr_info(self)
                elif i == "Primevideo":
                    from addons.unlockTest import primevideo
                    info['Primevideo'] = primevideo.get_primevideo_info(self)
                elif i == "Myvideo":
                    from addons.unlockTest import myvideo
                    info['Myvideo'] = myvideo.get_myvideo_info(self)
                elif i == "Catchplay":
                    from addons.unlockTest import catchplay
                    info['Catchplay'] = catchplay.get_catchplay_info(self)
                elif i == "Viu":
                    from addons.unlockTest import viu
                    info['Viu'] = viu.get_viu_info(self)
                elif i == "Iprisk" or i == "落地ip风险":
                    from addons import ip_risk
                    info['落地ip风险'] = ip_risk.get_iprisk_info(self)
                else:
                    pass
        except Exception as e:
            logger.error(str(e))
        return info

    def get_dazn_info(self):
        """

        :return: str: 解锁信息: [解锁(地区代码)、失败、N/A]
        """
        try:
            if 'dazn' not in self.data:
                logger.warning("采集器内无数据: Dazn")
                return "N/A"
            else:
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

    def get_bilibili_info(self):
        """

        :return: str: 解锁信息: [解锁(台湾)、解锁(港澳台)、失败、N/A]
        """
        try:
            if 'bilibili' not in self.data:
                logger.warning("采集器内无数据: bilibili")
                return "N/A"
            else:
                try:
                    info = self.data['bilibili']
                    if info is None:
                        logger.warning("无法读取bilibili解锁信息")
                        return "N/A"
                    else:
                        logger.info("bilibili情况: " + info)
                        return info
                except KeyError:
                    logger.warning("无法读取bilibili解锁信息")
                    return "N/A"
        except Exception as e:
            logger.error(e)
            return "N/A"

    # 以下为旧版奈飞测试，灵感来自 SSRSpeedN ，现已废弃。如果有人看到这段消息，可以删掉这段代码了。
    # def getnetflixinfo(self):
    #     """
    #
    #     :return: list: [netflix_ip, proxy_ip, netflix_info: "解锁"，“自制”，“失败”，“N/A”]
    #     """
    #     try:
    #         if self.data['ip'] is None or self.data['ip'] == "N/A":
    #             return ["N/A", "N/A", "N/A"]
    #         if self.data['netflix2'] is None:
    #             return ["N/A", "N/A", "N/A"]
    #         if self.data['netflix1'] is None:
    #             return ["N/A", "N/A", "N/A"]
    #         r1 = self.data['netflix1']
    #         status_code = self.data['ne_status_code1']
    #         if status_code == 200:
    #             self._sum += 1
    #             soup = BeautifulSoup(r1, "html.parser")
    #             netflix_ip_str = str(soup.find_all("script"))
    #             p1 = netflix_ip_str.find("requestIpAddress")
    #             netflix_ip_r = netflix_ip_str[p1 + 19:p1 + 60]
    #             p2 = netflix_ip_r.find(",")
    #             netflix_ip = netflix_ip_r[0:p2]
    #             self._netflix_info.append(netflix_ip)  # 奈飞ip
    #         r2 = self.data['ne_status_code2']
    #         if r2 == 200:
    #             self._sum += 1
    #
    #         self._netflix_info.append(self.data['ip']['ip'])  # 请求ip
    #
    #         if self._sum == 0:
    #             ntype = "失败"
    #             self._netflix_info.append(ntype)  # 类型有四种，分别是无、仅自制剧、原生解锁（大概率）、 DNS解锁
    #             logger.info("当前节点情况: " + str(self._netflix_info))
    #             return self._netflix_info
    #         elif self._sum == 1:
    #             ntype = "自制"
    #             self._netflix_info.append(ntype)
    #             logger.info("当前节点情况: " + str(self._netflix_info))
    #             return self._netflix_info
    #         elif self.data['ip']['ip'] == self._netflix_info[0]:
    #             text = self.data['netflix2']
    #             s = text.find('preferredLocale', 100000)
    #             if s == -1:
    #                 self._netflix_info.append("原生解锁(未知)")
    #                 logger.info("当前节点情况: " + str(self._netflix_info))
    #                 return self._netflix_info
    #             region = text[s + 29:s + 31]
    #             ntype = "原生解锁({})".format(region)
    #             self._netflix_info.append(ntype)
    #             logger.info("当前节点情况: " + str(self._netflix_info))
    #             return self._netflix_info
    #         else:
    #             text = self.data['netflix2']
    #             s = text.find('preferredLocale', 100000)
    #             if s == -1:
    #                 self._netflix_info.append("DNS解锁(未知)")
    #                 logger.info("当前节点情况: " + str(self._netflix_info))
    #                 return self._netflix_info
    #             region = text[s + 29:s + 31]
    #             ntype = "DNS解锁({})".format(region)
    #             self._netflix_info.append(ntype)
    #             logger.info("当前节点情况: " + str(self._netflix_info))
    #             return self._netflix_info
    #     except Exception as e:
    #         logger.error(e)
    #         return ["N/A", "N/A", "N/A"]

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
                    return "失败(CN)"
                elif self.data['youtube_status_code'] == 200:
                    idx = text.find('"countryCode"')
                    region = text[idx:idx + 17].replace('"countryCode":"', "")
                    if idx == -1 and text.find('manageSubscriptionButton') != -1:
                        region = "US"
                    elif region == "":
                        region == "未知"
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
            if self.data['disney'] is None:
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

    def start(self):
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
            if '延迟RTT' in self.data:
                rtt = self.data['延迟RTT']
                new_rtt = []
                for r in rtt:
                    new_rtt.append(str(r) + 'ms')
                self.data['延迟RTT'] = new_rtt
            return self.data
        except TypeError:
            return {}


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
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")  # 匹配订阅地址
    # 获取订阅地址
    try:
        url = pattern.findall(text)[0]  # 列表中第一个项为订阅地址
        return url
    except IndexError:
        logger.info("未找到URL")
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
