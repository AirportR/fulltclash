import aiohttp
import asyncio

from loguru import logger


@logger.catch()
async def get_ip(url, session, proxy):
    try:
        async with session.get(url, proxy=proxy) as response:
            if response.status == 200:
                return await response.text()
            else:
                return None
    except Exception as e:
        logger.info(str(e))
        return None


async def get_ips(proxyhost: list, proxyport: list):
    v4url = "http://v4.ipv6-test.com/api/myip.php"
    v6url = "http://v6.ipv6-test.com/api/myip.php"

    async with aiohttp.ClientSession() as session:
        tasks = []
        results = []
        for i in range(min(len(proxyhost), len(proxyport))):
            proxy = f"http://{proxyhost[i]}:{proxyport[i]}"
            tasks.append(asyncio.ensure_future(get_ip(v4url, session, proxy)))
            tasks.append(asyncio.ensure_future(get_ip(v6url, session, proxy)))
            # await asyncio.sleep(0.1)
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
    return results
