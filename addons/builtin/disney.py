import ssl

import aiohttp
import json
import asyncio

from loguru import logger
from utils import retry

cookie = 'grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Atoken-exchange&latitude=0&longitude=0&' \
         'platform=browser&subject_token=DISNEYASSERTION&subject_token_type=' \
         'urn%3Abamtech%3Aparams%3Aoauth%3Atoken-type%3Adevice'
assertion = '{"deviceFamily":"browser","applicationRuntime":"chrome","deviceProfile":"windows","attributes":{}}'
authbear = 'Bearer ZGlzbmV5JmJyb3dzZXImMS4wLjA.Cu56AgSfBTDag5NiRA81oLHkDZfu5L3CKadnefEAY84'
ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
gql = '{"query":"mutation refreshToken($input: RefreshTokenInput!) {refreshToken(refreshToken: $input) {' + \
      'activeSession {sessionId}}}","variables":{"input":{"refreshToken":"ILOVEDISNEY"}}}'


@retry(2)
async def fetch_disney(collector, session: aiohttp.ClientSession, proxy=None):
    conn = session.connector
    if type(conn).__name__ == 'ProxyConnector':
        proxy = "http://" + conn._proxy_host + ":" + str(conn._proxy_port)
    async with aiohttp.ClientSession() as session2:
        headers = {
            'User-Agent': ua,
            'Authorization': authbear,
            'Content-Type': 'application/json',
        }
        assertion_token = await fetch(session2, 'https://disney.api.edge.bamgrid.com/devices', headers=headers,
                                      data=assertion, proxy=proxy, ssl=myssl())
        assertion_token_json = json.loads(assertion_token)
        assertion_cookie = cookie.replace('DISNEYASSERTION', assertion_token_json.get('assertion', ''))

        headers = {
            'User-Agent': ua,
            'Authorization': authbear,
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        token_response = await fetch(session2, 'https://disney.api.edge.bamgrid.com/token', headers=headers,
                                     data=assertion_cookie, proxy=proxy, ssl=myssl())
        token_json = json.loads(token_response)
        if token_json.get('error_description') == 'forbidden-location':
            collector.info["disney"] = '失败'
            return True

        elif not token_json:
            collector.info["disney"] = 'N/A'
            return True

        elif not token_json.get('refresh_token'):
            collector.info["disney"] = 'N/A'
            return True
        else:
            payload = gql.replace('ILOVEDISNEY', token_json['refresh_token'])
            headers = {
                'User-Agent': ua,
                'Authorization': authbear,
            }
            content = await fetch(session2, 'https://disney.api.edge.bamgrid.com/graph/v1/device/graphql',
                                  headers=headers, data=payload, proxy=proxy, ssl=myssl())

            headers = {
                'User-Agent': ua,
            }
            url1 = "https://disneyplus.com"
            try:
                # 这个请求有个奇怪的问题，有些节点无法请求成功，可能是py请求库的问题，留待以后解决。如果抛异常，那么检测结果的准确度有所下降。
                async with session2.get(url1, headers=headers, proxy=proxy, timeout=5,
                                        allow_redirects=False, ssl=myssl()) as resp:
                    unavailable_response = await resp.text()
            except Exception as e:
                unavailable_response = str(e)
            preview_check = 'preview' in unavailable_response
            unavailable = 'unavailable' in unavailable_response if preview_check else False

            content_data = json.loads(content)
            region = (content_data.get('extensions', {}).get('sdk', {}).get('session', {}).get('location', {}).get(
                'countryCode', '').upper() or '')
            in_supported_location = content_data.get('extensions', {}).get('sdk', {}).get('session', {}).get(
                'inSupportedLocation', False)

            if region == 'JP':
                collector.info["disney"] = '解锁(JP)'
            elif region and not in_supported_location and not unavailable:
                collector.info["disney"] = f'待解锁({region})'
            elif region and unavailable:
                collector.info["disney"] = f'失败({region})'
            elif region and in_supported_location:
                collector.info["disney"] = f'解锁({region})'
            else:
                collector.info["disney"] = '未知'
            return True


async def fetch(session, url, *, headers=None, data=None, proxy=None, timeout=5, **kwargs):
    async with session.request(method='POST', url=url, headers=headers, data=data, proxy=proxy, timeout=timeout,
                               **kwargs) as resp:
        return await resp.text()


def task(collector, session, proxy):
    return asyncio.create_task(fetch_disney(collector, session, proxy=proxy))


def get_disney_info(ReCleaner):
    """
    获得解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁、失败、N/A]
    """
    try:
        if 'disney' not in ReCleaner.data:
            return "N/A"
        else:
            return ReCleaner.data.get('disney', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


def myssl() -> ssl.SSLContext:
    _myssl = ['DH+3DES', 'ECDH+3DES', 'RSA+3DES', 'RSA+HIGH', 'RSA+AES', 'ECDH+AESGCM', 'DH+AES256', 'ECDH+HIGH',
              'DH+AESGCM', 'ECDH+AES256', 'RSA+AESGCM', 'ECDH+AES128', 'DH+HIGH', 'DH+AES']
    _ciphers = ":".join(_myssl)
    _sslcontext = ssl.create_default_context()
    _sslcontext.set_ciphers(_ciphers)
    return _sslcontext


SCRIPT = {
    "MYNAME": "Disney+",
    "TASK": task,
    "GET": get_disney_info,
    "RANK": 0.2
}


async def demo():
    from utils import script_demo
    await script_demo(fetch_disney, proxy='http://127.0.0.1:11112')


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(demo())
