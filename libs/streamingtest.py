import asyncio
import time

import requests.exceptions
from pyrogram.errors import RPCError, FloodWait
from loguru import logger
from libs import cleaner, collector, export, proxys, check

"""
这个模块是流媒体测试的具体实现
"""


async def unit(test_items: list, delay: int):
    """
    以一个节点的所有测试项为一个基本单元unit,返回单个节点的测试结果
    :param test_items:
    :param delay: 节点延迟，可选参数，若为0，则测试项全部返回N/A
    :return: list 返回test_items对应顺序的信息
    """
    info = []
    if delay == 0:
        for _ in test_items:
            info.append("N/A")
        return info
    else:
        cl = collector.Collector()
        re1 = await cl.start(proxy="http://127.0.0.1:{}".format(1122))
        cnr = cleaner.ReCleaner(re1)
        old_info = cnr.get_all()
        for item in test_items:
            i = item.capitalize()
            try:
                info.append(old_info[i])
            except KeyError:
                info.append("N/A")
                logger.error("KeyError: 无法找到 " + item + " 测试项")
        return info


async def batch_test(message, nodename: list, delays: list, test_items: list, proxygroup='auto'):
    """
    批量测试
    :param test_items: 测试条目
    :param message: 消息对象
    :param nodename: 一组节点名称
    :param delays: 一组延迟
    :param proxygroup: 代理组，默认即可
    :return: dict 测试项批量测试的结果
    """
    info = {}
    progress = 0
    sending_time = 0
    nodenum = len(nodename)
    for item in test_items:
        info[item] = []
    for name in nodename:
        proxys.switchProxy_old(proxyName=name, proxyGroup=proxygroup, clashPort=1123)
        res = await unit(test_items, delays[progress])
        for i in range(len(test_items)):
            info[test_items[i]].append(res[i])
        progress += 1
        cal = progress / nodenum * 100
        # 判断进度条，每隔10%发送一次反馈，有效防止洪水等待(FloodWait)
        if cal > sending_time:
            await check.progress(message, progress, nodenum, cal)
            sending_time += 20
    return info


async def core(message, back_message, start_time, suburl: str = None, media_items: list = None):
    """

    :param message: 发起测试任务的对象
    :param back_message: 回复的消息对象
    :param start_time: 任务生成时间，取名用的
    :param suburl: 订阅地址,没有则尝试从配置文件匹配
    :param media_items: 测试的流媒体选项
    :return:
    """
    info = {}  # 存放Netflix Youtube 等等
    if media_items is None:
        test_items = collector.media_items
    else:
        test_items = media_items
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
            nodename = cl.nodesName()
            nodetype = cl.nodesType()
            nodenum = cl.nodesCount()
    except Exception as e:
        logger.error(e)
        nodename = None
        nodetype = None
        nodenum = None
    # 检查获得的数据
    if await check.check_nodes(back_message, nodenum, (nodename, nodetype,)):
        return
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    ma.addsub(subname=start_time, subpath='./sub{}.yaml'.format(start_time))
    ma.save('./clash/proxy.yaml')
    # 重载配置文件
    await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=1123)
    logger.info("开始测试延迟...")
    s1 = time.time()
    old_rtt = await collector.delay_providers(providername=start_time)
    rtt = check.check_rtt(old_rtt, nodenum)
    print("延迟:", rtt)
    # 启动流媒体测试
    try:
        info['节点名称'] = nodename
        test_info = await batch_test(back_message, nodename, rtt, test_items=test_items)
        info['类型'] = nodetype
        info['延迟RTT'] = rtt
        info.update(test_info)
        info = cleaner.ResultCleaner(info).start()
        # 计算测试消耗时间
        wtime = "%.1f" % float(time.time() - s1)
        info['wtime'] = wtime
        # 保存结果
        cl1 = cleaner.ConfigManager(configpath=r"./results/{}.yaml".format(start_time.replace(':', '-')), data=info)
        cl1.save(r"./results/{}.yaml".format(start_time.replace(':', '-')))
        # 生成图片
        try:
            stime = export.ExportResult(nodename=nodename, info=info).exportUnlock()
            # 发送回TG
            await check.check_photo(message, back_message, stime, nodenum, wtime)
        except requests.exceptions.ConnectionError:
            # 出现这个异常大概率是因为 pilmoji这个库抽风了
            stime = ''
            # 遇到错误就发送错误信息给TG
            await check.check_photo(message, back_message, stime, nodenum, wtime)
    except RPCError as r:
        logger.error(r)
        await back_message.edit_message_text("出错啦")
    except KeyboardInterrupt:
        await message.reply("程序已被强行中止")
    except FloodWait as e:
        logger.error(str(e))
        await asyncio.sleep(e.value)
    finally:
        return info

