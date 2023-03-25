import re
import random
import urllib
import urllib.parse
import aiohttp
import requests
import string
from loguru import logger
from aiohttp.client_exceptions import ClientConnectorError
from libs.cleaner import geturl
from libs.collector import proxies
import botmodule.init_bot

USER_TARGET = botmodule.init_bot.USER_TARGET


def random_value(length):
    num_set = [chr(i) for i in range(48, 58)]
    char_set = [chr(i) for i in range(97, 123)]
    total_set = num_set + char_set
    value_set = "".join(random.sample(total_set, length))
    return value_set

proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890'
}

class sspanel():
    def __init__(self,url,proxy=None):
        self._proxies = proxy
        self._name=''
        self._url = url
        self._reg_url=''
        self._login_url = ''
        self._user_url = ''
        self._sub=''
    
    def set_env(self):
        self._name = urllib.parse.urlparse(self._url).netloc
        self._reg_url = 'https://' + self._name + '/auth/register'
        self._login_url = 'https://' + self._name + '/auth/login'
        self._user_url = 'https://' + self._name + '/user'

    def register(self,email,password):
        headers= {
            "User-Agent":'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
            "referer": self._reg_url
        }
        data={
            "email":email,
            "name":password,
            "passwd":password,
            "repasswd":password,
            "invite_code":None,
            "email_code":None
        }
        geetest={
                "geetest_challenge": "98dce83da57b0395e163467c9dae521b1f",
                "geetest_validate": "bebe713_e80_222ebc4a0",
                "geetest_seccode": "bebe713_e80_222ebc4a0|jordan"}
        data.update(geetest)
        with requests.session() as session:
            resp = session.post(self._reg_url,headers=headers,data=data,timeout=5,proxies=self._proxies)

            data ={
                'email': email,
                'passwd': password,
                'code': '',
                'remember_me': 1,
            }
            try:
                resp = session.post(self._login_url,headers=headers,data=data,timeout=5,proxies=self._proxies)
            except:
                pass

            resp = session.get(self._user_url,headers=headers,timeout=5,proxies=self._proxies)
            try:
                token = re.search("https?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+clash=1", resp.text).group(0)
            except:
                token= re.search("https?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+sub=3", resp.text).group(0)
            self._sub = token
        return token

        
    def getSubscribe(self):
        password=''.join(random.sample(string.ascii_letters + string.digits + string.ascii_lowercase, 10))
        email=password+"@gmail.com"
        subscribe=self.register(email,password)
        return subscribe

class v2board():
    def __init__(self,url,proxy=None):
        self._proxies = proxy
        self._name=''
        self._url = url
        self._reg_url=''
        self._sub=''
    
    def set_env(self):
        self._name = urllib.parse.urlparse(self._url).netloc
        self._reg_url = 'https://' + self._name + '/api/v1/passport/auth/register'
        self._sub = 'https://' + self._name + '/api/v1/client/subscribe?token={token}'

    def register(self,email,password):
        headers= {
            "User-Agent":'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
            "Refer": self._url
        }
        data={
            "email":email,
            "password":password,
            "invite_code":None,
            "email_code":None
        }
        req=requests.post(self._reg_url,headers=headers,data=data,timeout=5,proxies=self._proxies)
        return req
        
    def getSubscribe(self):
        password=''.join(random.sample(string.ascii_letters + string.digits + string.ascii_lowercase, 10))
        email=password+"@gmail.com"
        req=self.register(email,password)
        token=req.json()["data"]["token"]
        subscribe=self._sub.format(token=token)
        return subscribe

async def getsub_async(url: str, username: str, pwd: str, proxy=None):
    """
    获取无邮箱验证的机场订阅,目前支持v2board 和 sspanel
    :param proxy: 代理
    :param url: 机场注册地址 如："https://feiniaoyun.xyz/api/v1/passport/auth/register"
    :param username: 用户名
    :param pwd: 密码
    :return: 订阅地址
    """
    async with aiohttp.ClientSession() as session:
        try:
            try :
                v2b = v2board(url)
                v2b.set_env()
                link = v2b.getSubscribe()
                return link
            except :
                try :
                    ss = sspanel(url)
                    ss.set_env()
                    link = ss.getSubscribe()
                    return link
                except :
                    return None
               
        except Exception as e:
            logger.error(str(e))
            return str(e)


async def baipiao(_, message):
    back_message = await message.reply("正在尝试注册...")  # 发送提示
    regisurl = geturl(str(message.text))
    if regisurl:
        suburl = await getsub_async(regisurl, random_value(10), random_value(8), proxy=proxies)
    else:
        await back_message.edit_text("❌发生错误，请检查注册地址是否正确")
        return
    if suburl:
        await back_message.edit_text(suburl)
        return
    else:
        await back_message.edit_text("❌发生错误，请检查注册地址是否正确")
        return
