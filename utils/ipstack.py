import aiohttp
import asyncio
from loguru import logger
from aiohttp_socks import ProxyConnector, ProxyConnectionError


async def get_ip(url, session):
    try:
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                return await response.text()
            else:
                return None
    except (ProxyConnectionError, asyncio.TimeoutError):
        return None
    except aiohttp.ServerDisconnectedError:
        return None
    except Exception as e:
        logger.error(str(e))
        return None


async def get_ips(proxyhost: list, proxyport: list):
    v4url = "http://v4.ipv6-test.com/api/myip.php"
    v6url = "http://v6.ipv6-test.com/api/myip.php"

    tasks = []
    results = []
    session_pool = []
    length = min(len(proxyhost), len(proxyport))
    for i in range(length):
        conn = ProxyConnector(host=proxyhost[i], port=proxyport[i], limit=0)
        session = aiohttp.ClientSession(connector=conn, headers={'user-agent': 'FullTclash'})
        session_pool.append(session)
    for j in range(length):
        tasks.append(asyncio.create_task(get_ip(v4url, session=session_pool[j])))
        tasks.append(asyncio.create_task(get_ip(v6url, session=session_pool[j])))
    for i in range(0, len(tasks), 2):
        res1, res2 = await asyncio.gather(tasks[i], tasks[i + 1])
        if res1 and res2:
            if '.' in res1 and ':' in res2 or ':' in res1 and '.' in res2:
                results.append('46')
            elif ':' in res2:
                results.append('6')
            elif '.' in res1:
                results.append('4')
            else:
                results.append('N/A')
        elif res1:
            results.append('4')
        elif res2:
            results.append('6')
        else:
            results.append('N/A')
    for session in session_pool:
        await session.close()
    return results
