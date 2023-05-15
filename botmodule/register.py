import random
import urllib.parse
import aiohttp
from loguru import logger
from aiohttp.client_exceptions import ClientConnectorError
from utils.cleaner import geturl
from utils.collector import proxies
import botmodule.init_bot

USER_TARGET = botmodule.init_bot.USER_TARGET


def random_value(length):
    num_set = [chr(i) for i in range(48, 58)]
    char_set = [chr(i) for i in range(97, 123)]
    total_set = num_set + char_set
    value_set = "".join(random.sample(total_set, length))
    return value_set


async def getsub_async(url: str, username: str, pwd: str, proxy=None):
    """
    获取无邮箱验证的机场订阅,目前仅支持v2board
    :param proxy: 代理
    :param url: 机场注册地址 如："https://feiniaoyun.xyz/api/v1/passport/auth/register"
    :param username: 用户名
    :param pwd: 密码
    :return: 订阅地址
    """
    _headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/102.0.5005.63 Safari/537.36'}
    domain = urllib.parse.urlparse(url).netloc
    data = {"email": username + "@qq.com", "password": pwd}
    apiurl = 'https://{}/api/v1/passport/auth/register'.format(domain)
    async with aiohttp.ClientSession() as session:
        try:
            resp = await session.post(url=apiurl, data=data, proxy=proxy, timeout=5, headers=_headers)
            if resp.status == 200:
                text = await resp.json()
                try:
                    print(text)
                    res = text.get('data', {}).get('token', '')
                    # res = text.split('token":"')[1].split('","auth_data')[0]
                except IndexError:
                    res = ''
                except AttributeError:
                    res = ''
                if len(res) < 1:
                    return None
                suburl = f"https://{domain}/api/v1/client/subscribe?token=" + res
                return suburl
            else:
                return None
        except ClientConnectorError as c:
            logger.warning("注册请求发生错误:" + str(c))
            return str(c)
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
