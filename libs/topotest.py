import asyncio
import time

import aiohttp
from loguru import logger
from pyrogram.errors import RPCError, FloodWait

from libs import cleaner, collector, sorter, check, proxys

"""
这个模块是拓扑测试（出入口落地分析）的具体实现
"""
proxies = collector.proxies


async def topo(file_path: str):
    info = {'地区': [], 'AS编号': [], '组织': [], '入口ip段': []}
    cl = cleaner.ClashCleaner(file_path)
    co = collector.IPCollector()
    session = aiohttp.ClientSession()
    nodename, inboundinfo, cl = sorter.sort_nodename_topo(cl)
    if nodename and inboundinfo and cl:
        # 拿地址，已经转换了域名为ip,hosts变量去除了N/A
        hosts = list(inboundinfo.keys())
        # 创建任务并开始采集ip信息
        co.create_tasks(session=session, hosts=hosts, proxy=proxies)
        res = await co.start()
        await session.close()
        if res:
            country_code = []
            asn = []
            org = []
            for j in res:
                ipcl = cleaner.IPCleaner(j)
                country_code.append(ipcl.get_country_code())
                asn.append(str(ipcl.get_asn()))
                org.append(ipcl.get_org())
            info.update({'地区': country_code, 'AS编号': asn, '组织': org})
            numcount = []
            for v in inboundinfo.values():
                numcount.append(str(v))
            new_hosts = []
            for host in hosts:
                if len(host) < 16:  # v4地址最大长度为15
                    try:
                        old_ip = host.split('.')[:2]
                        new_ip = old_ip[0] + "." + old_ip[1] + ".*.*"
                    except IndexError:
                        new_ip = host
                    new_hosts.append(new_ip)
                else:
                    new_hosts.append(host)
            info.update({'入口ip段': new_hosts})
            info.update({'出口数量': numcount})
        return info, hosts, cl


@logger.catch()
async def batch_topo(message, nodename: list, pool: dict, proxygroup='auto'):
    resdata = []
    progress = 0
    sending_time = 0
    host = pool.get('host', [])
    port = pool.get('port', [])
    psize = len(port)
    nodenum = len(nodename)
    logger.info("接受任务数量: {} 线程数: {}".format(nodenum, psize))
    if psize <= 0:
        logger.error("无可用的代理程序接口")
        return []
    await check.progress(message, 0, nodenum, 0, "╰(*°▽°*)╯节点链路拓扑测试进行中...")
    if nodenum < psize:
        for i in range(nodenum):
            proxys.switchProxy_old(proxyName=nodename[i], proxyGroup=proxygroup, clashHost=host[i],
                                   clashPort=port[i] + 1)
        ipcol = collector.IPCollector()
        sub_res = await ipcol.batch(proxyhost=host[:nodenum], proxyport=port[:nodenum])
        resdata.extend(sub_res)
        return resdata
    else:
        subbatch = nodenum // psize
        for s in range(subbatch):
            logger.info("当前批次: " + str(s + 1))
            for i in range(psize):
                proxys.switchProxy_old(proxyName=nodename[s * psize + i], proxyGroup=proxygroup, clashHost=host[i],
                                       clashPort=port[i] + 1)
            ipcol = collector.IPCollector()
            sub_res = await ipcol.batch(proxyhost=host, proxyport=port)
            resdata.extend(sub_res)
            # 反馈进度

            progress += psize
            cal = progress / nodenum * 100
            # 判断进度条，每隔10%发送一次反馈，有效防止洪水等待(FloodWait)
            if cal > sending_time:
                await check.progress(message, progress, nodenum, cal, "╰(*°▽°*)╯节点链路拓扑测试进行中...")
                sending_time += 20

        if nodenum % psize != 0:
            logger.info("最后批次: " + str(subbatch + 1))
            for i in range(nodenum % psize):
                proxys.switchProxy_old(proxyName=nodename[subbatch * psize + i], proxyGroup=proxygroup, clashHost=host[i],
                                       clashPort=port[i] + 1)
            ipcol = collector.IPCollector()
            sub_res = await ipcol.batch(proxyhost=host[:nodenum % psize],
                                        proxyport=port[:nodenum % psize])
            resdata.extend(sub_res)

        # 最终进度条
        if nodenum % psize != 0:
            await check.progress(message, nodenum, nodenum, 100, "╰(*°▽°*)╯节点链路拓扑测试进行中...")
        return resdata


async def core(message, back_message, start_time, suburl: str = None, test_type="all", thread: int = 1):
    """

    :param thread: 测试线程
    :param message:
    :param back_message:
    :param start_time: 测试时间
    :param suburl: 订阅链接，没有会尝试从message中获取
    :param test_type: 测试类型，有三种：[仅入口，仅出口，全部]，默认测试全部
    :return:
    """
    info1 = {}
    info2 = {}
    include_text = ''
    exclude_text = ''
    if suburl is not None:
        url = suburl
        text = str(message.text)
        texts = text.split(' ')
        if len(texts) > 2:
            include_text = texts[2]
        if len(texts) > 3:
            exclude_text = texts[3]
    else:
        text = str(message.text)
        url = cleaner.geturl(text)
        texts = text.split(' ')
        if len(texts) > 2:
            include_text = texts[2]
        if len(texts) > 3:
            exclude_text = texts[3]
    if await check.check_url(back_message, url):
        return info1, info2
    print(url)
    pool = {'host': ['127.0.0.1' for _ in range(thread)],
            'port': [1124 + t * 2 for t in range(thread)]}
    # 订阅采集
    logger.info(f"过滤器: 包含: [{include_text}], 排除: [{exclude_text}]")
    sub = collector.SubCollector(suburl=url, include=include_text, exclude=exclude_text)
    subconfig = await sub.getSubConfig(save_path='./clash/sub{}.yaml'.format(start_time))
    if await check.check_sub(back_message, subconfig):
        return info1, info2
    try:
        # 启动订阅清洗
        with open('./clash/sub{}.yaml'.format(start_time), "r", encoding="UTF-8") as fp:
            cl = cleaner.ClashCleaner(fp)
            nodenum = cl.nodesCount()
    except Exception as e:
        logger.error(e)
        nodenum = 0
    # 检查获得的数据
    if await check.check_nodes(back_message, nodenum, ()):
        return info1, info2
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    ma.addsub(subname=start_time, subpath='./sub{}.yaml'.format(start_time))
    ma.save('./clash/proxy.yaml')
    # 重载配置文件
    await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=1123)
    try:
        if nodenum < len(pool.get('port', [])):
            for i in pool.get('port', [])[:nodenum]:
                await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=i + 1)
        else:
            for i in pool.get('port', []):
                await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=i + 1)
    except Exception as e:
        logger.error(str(e))
        return info1, info2
    s1 = time.time()
    info1, hosts, cl = await topo('./clash/sub{}.yaml'.format(start_time))
    nodename = cl.nodesName()
    cl2 = cleaner.ConfigManager(configpath=r"./results/Topo{}-inbound.yaml".format(start_time.replace(':', '-')),
                                data=info1)
    cl2.save(r"./results/Topo{}-inbound.yaml".format(start_time.replace(':', '-')))
    if test_type == "inbound":
        wtime = "%.1f" % float(time.time() - s1)
        info1['wtime'] = wtime
        logger.info(info2)
        return info1, info2

    # 启动链路拓扑测试
    try:
        info2 = {}
        res = await batch_topo(back_message, nodename, pool)
        if res:
            country_code = []
            asn = []
            org = []
            ipaddr = []
            for j in res:
                ipcl = cleaner.IPCleaner(j)
                country_code.append(ipcl.get_country_code())
                asn.append(str(ipcl.get_asn()))
                org.append(ipcl.get_org())
                ip = ipcl.get_ip()
                if len(ip) < 16:  # v4地址最大长度为15
                    try:
                        old_ip = ip.split('.')
                        new_ip = "*.*.*." + old_ip[-1]
                    except IndexError:
                        new_ip = ip
                    ipaddr.append(new_ip)
                else:
                    ipaddr.append("?")

            info2.update({'地区': country_code, 'AS编号': asn, '组织': org, '出口ip': ipaddr})
            info2.update({'节点名称': nodename})
        # 计算测试消耗时间
        wtime = "%.1f" % float(time.time() - s1)
        info2.update({'wtime': wtime})
        cl1 = cleaner.ConfigManager(configpath=r"./results/Topo{}-outbound.yaml".format(start_time.replace(':', '-')),
                                    data=info2)
        cl1.save(r"./results/Topo{}-outbound.yaml".format(start_time.replace(':', '-')))

    except RPCError as r:
        logger.error(r)
        await back_message.edit_message_text("出错啦")
    except KeyboardInterrupt:
        await message.reply("程序已被强行中止")
    except FloodWait as e:
        logger.error(str(e))
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(str(e))
        await message.reply(str(e))
    finally:
        logger.info(str(info2))
        return info1, info2


if __name__ == "__main__":
    print("this is a demo")
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)


    async def test():
        a = await batch_topo(['🇺🇸 USA-01-1x', '🇭🇰 HKG-02-1x', '🇭🇰 HKG-03-1x', '🇸🇬 SGP-02-IPLC', '🇸🇬 SGP-01-IPLC'],
                         {'host': ['127.0.0.1' for _ in range(4)], 'port': [1112, 1114, 1116, 1118]}, 'ETON')
        print(a)

    loop.run_until_complete(test())
