import asyncio
import time

import aiohttp
from loguru import logger
from pyrogram.errors import RPCError, FloodWait

from libs import cleaner, collector, sorter, check, proxys, export
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


async def core(client, message, back_message, start_time, suburl: str = None, test_type="all"):
    """

    :param client:
    :param message:
    :param back_message:
    :param start_time:
    :param suburl:
    :param test_type: 测试类型，有三种：[仅入口，仅出口，全部]，默认测试全部
    :return:
    """
    if suburl is not None:
        url = suburl
    else:
        text = str(message.text)
        url = cleaner.geturl(text)
        if await check.check_url(back_message, url):
            return
    print(url)
    # 订阅采集
    sub = collector.SubCollector(suburl=url)
    subconfig = await sub.getSubConfig(save_path='./clash/sub{}.yaml'.format(start_time))
    if await check.check_sub(back_message, subconfig):
        return
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
        return
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    ma.addsub(subname=start_time, subpath='./sub{}.yaml'.format(start_time))
    ma.save('./clash/proxy.yaml')
    # 重载配置文件
    await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=1123)

    s1 = time.time()
    info1, hosts, cl = await topo('./clash/sub{}.yaml'.format(start_time))
    wtime = "%.1f" % float(time.time() - s1)
    nodename = cl.nodesName()
    if test_type == "inbound":
        stime = export.ExportTopo(name=hosts, info=info1).exportTopoInbound()
        await check.check_photo(message, back_message, 'Topo' + stime, len(hosts), wtime)
        return

    # 启动链路拓扑测试
    try:
        info2 = {}

        res = []
        progress = 0
        sending_time = 0
        for name in nodename:
            session = aiohttp.ClientSession()
            proxys.switchProxy_old(name, proxyGroup="auto", clashPort=1123)
            ipcol = collector.IPCollector()
            ipcol.create_tasks(session, proxy="http://127.0.0.1:1122")
            sub_res = await ipcol.start()
            await session.close()
            if sub_res:
                res.append(sub_res[0])
            else:
                res.append([])

            progress += 1
            cal = progress / nodenum * 100
            p_text = "%.2f" % cal
            # 判断进度条，每隔10%发送一次反馈，有效防止洪水等待(FloodWait)
            if cal >= sending_time:
                sending_time += 10
                try:
                    await back_message.edit_text("╰(*°▽°*)╯节点链路拓扑测试进行中...\n\n" +
                                                 "当前进度:\n" + p_text +
                                                 "%     [" + str(progress) + "/" + str(nodenum) + "]")  # 实时反馈进度
                except RPCError as r:
                    logger.error(r)

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
        # 生成图片
        img_outbound, yug, image_width2 = export.ExportTopo().exportTopoOutbound(nodename=nodename, info=info2)
        if test_type == "outbound":
            stime = export.ExportTopo(name=nodename, info=info2).exportTopoOutbound()
        else:
            stime = export.ExportTopo(name=hosts, info=info1).exportTopoInbound(nodename, info2, img2_width=image_width2)
        # 发送回TG
        await check.check_photo(message, back_message, 'Topo' + stime, nodenum, wtime)
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
