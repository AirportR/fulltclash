import loguru
import requests
import random
import urllib.parse

from libs.cleaner import geturl
import botmodule.init_bot

USER_TARGET = botmodule.init_bot.USER_TARGET


def random_value(length):
    num_set = [chr(i) for i in range(48, 58)]
    char_set = [chr(i) for i in range(97, 123)]
    total_set = num_set + char_set
    value_set = "".join(random.sample(total_set, length))
    return value_set


def getsub(url: str, username: str, pwd: str):
    """
    获取无邮箱验证的机场订阅,目前仅支持v2board
    :param url: 机场注册地址 如："https://feiniaoyun.xyz/api/v1/passport/auth/register"
    :param username: 用户名
    :param pwd: 密码
    :return: 订阅地址
    """

    domain = urllib.parse.urlparse(url).netloc
    data = {"email": username + "@qq.com", "password": pwd}
    apiurl = 'https://{}/api/v1/passport/auth/register'.format(domain)
    try:
        co = requests.post(url=apiurl, data=data)
        body = co.text
    except Exception as e:
        loguru.logger.error(str(e))
        body = ""
    try:
        res = body.split('token":"')[1].split('","auth_data')[0]
    except IndexError:
        res = ''
    suburl = "https://{}/api/v1/client/subscribe?token=".format(domain) + res
    if len(res) < 1:
        return None
    return suburl


async def baipiao(client, message):
    global USER_TARGET
    try:
        if int(message.from_user.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    except AttributeError:
        if int(message.sender_chat.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    back_message = await message.reply("正在尝试注册...")  # 发送提示
    regisurl = geturl(str(message.text))
    if regisurl:
        suburl = getsub(regisurl, random_value(10), random_value(8))
    else:
        await back_message.edit_text("❌发生错误，请检查注册地址是否正确")
        return
    if suburl:
        await back_message.edit_text(suburl)
        return
    else:
        await back_message.edit_text("❌发生错误，请检查注册地址是否正确")
        return

