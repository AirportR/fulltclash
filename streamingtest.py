import asyncio
import time
from pyrogram.errors import RPCError, FloodWait
from loguru import logger
from libs import cleaner, collector, export, proxys, check


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
        p_text = "%.2f" % cal
        # 判断进度条，每隔10%发送一次反馈，有效防止洪水等待(FloodWait)
        if cal >= sending_time:
            sending_time += 10
            try:
                await message.edit_text("╰(*°▽°*)╯流媒体测试进行中...\n\n" +
                                        "当前进度:\n" + p_text +
                                        "%     [" + str(progress) + "/" + str(nodenum) + "]")  # 实时反馈进度
            except RPCError as r:
                logger.error(r)
    return info


async def core(client, message, back_message, test_members, start_time, suburl: str = None):
    logger.info("当前序号:" + str(test_members))
    info = {}  # 存放Netflix Youtube 等等
    if await check.check_number(back_message, test_members):
        return
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
    # 检查获得的数据
    if await check.check_nodes(back_message, nodenum, (nodename, nodetype,)):
        return
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    ma.addsub(subname=start_time, subpath='./sub{}.yaml'.format(start_time))
    ma.save('./clash/proxy.yaml')
    # 重载配置文件
    await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=1123)
    s1 = time.time()
    old_rtt = await collector.delay_providers(providername=start_time)
    rtt = check.check_rtt(old_rtt, nodenum)
    print("延迟:", rtt)
    # 启动流媒体测试
    try:
        test_info = await batch_test(back_message, nodename, rtt, ['Netflix', 'Youtube', 'Disney+', 'Bilibili', 'Dazn'])
        info['类型'] = nodetype
        info['延迟RTT'] = rtt
        info.update(test_info)
        info = cleaner.ResultCleaner(info).start()
        # 计算测试消耗时间
        wtime = "%.1f" % float(time.time() - s1)
        info['wtime'] = wtime
        # 生成图片
        stime = export.ExportResult(nodename=nodename, info=info).exportAsPng()
        # 发送回TG
        await check.check_photo(message, back_message, stime, nodenum, wtime)
    except RPCError as r:
        logger.error(r)
        await back_message.edit_message_text("出错啦")
    except KeyboardInterrupt:
        await message.reply("程序已被强行中止")
    except FloodWait as e:
        logger.error(str(e))
        await asyncio.sleep(e.value)


async def old_core(client, message, back_message, test_members, start_time, suburl: str = None):
    logger.info("当前序号:" + str(test_members))
    progress = 0
    sending_time = 0
    proxy_group = 'auto'
    info = {}  # 存放Netflix Youtube 等等
    if await check.check_number(back_message, test_members):
        return
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
    # 检查获得的数据
    if await check.check_nodes(back_message, nodenum, (nodename, nodetype,)):
        return

    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    ma.addsub(subname=start_time, subpath='./sub{}.yaml'.format(start_time))
    ma.save('./clash/proxy.yaml')
    # 重载配置文件
    await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=1123)
    # 进入循环，直到所有任务完成
    ninfo = []  # 存放所测节点Netflix的解锁信息
    youtube_info = []
    disneyinfo = []
    s1 = time.time()
    old_rtt = await collector.delay_providers(providername=start_time)
    rtt = check.check_rtt(old_rtt, nodenum)
    print("延迟:", rtt)
    rtt_num = 0
    # 启动流媒体测试
    try:
        for n in nodename:
            if rtt[rtt_num] == 0:
                logger.info("超时节点，跳过测试......")
                youtube_info.append("N/A")
                ninfo.append("N/A")
                disneyinfo.append("N/A")
                rtt_num += 1
                progress += 1
                cal = progress / nodenum * 100
                p_text = "%.2f" % cal
                if cal >= sending_time:
                    sending_time += 10
                    await back_message.edit_text("╰(*°▽°*)╯流媒体测试进行中...\n\n" +
                                                 "当前进度:\n" + p_text +
                                                 "%     [" + str(progress) + "/" + str(nodenum) + "]")  # 实时反馈进度
                continue
            proxys.switchProxy_old(proxyName=n, proxyGroup=proxy_group, clashPort=1123)
            progress += 1
            cl = collector.Collector()
            n1 = await cl.start(proxy="http://127.0.0.1:{}".format(1122))
            clean = cleaner.ReCleaner(n1)
            nf = clean.getnetflixinfo()
            ninfo.append(nf[len(nf) - 1])
            you = clean.getyoutubeinfo()
            youtube_info.append(you)
            dis = clean.getDisneyinfo()
            disneyinfo.append(dis)
            rtt_num += 1
            cal = progress / nodenum * 100
            p_text = "%.2f" % cal
            # 判断进度条，每隔10%发送一次反馈，有效防止洪水等待(FloodWait)
            if cal >= sending_time:
                sending_time += 10
                await back_message.edit_text("╰(*°▽°*)╯流媒体测试进行中...\n\n" +
                                             "当前进度:\n" + p_text +
                                             "%     [" + str(progress) + "/" + str(nodenum) + "]")  # 实时反馈进度
        info['类型'] = nodetype
        info['延迟RTT'] = rtt
        # 过滤None值
        new_n = cleaner.replace(ninfo, None, "N/A")
        new_y = cleaner.replace(youtube_info, None, "N/A")
        new_dis = cleaner.replace(disneyinfo, None, "N/A")
        info['Netflix'] = new_n
        info['Youtube'] = new_y
        info['Disney+'] = new_dis
        info = cleaner.ResultCleaner(info).start()
        # 计算测试消耗时间
        wtime = "%.1f" % float(time.time() - s1)
        info['wtime'] = wtime
        # 生成图片
        stime = export.ExportResult(nodename=nodename, info=info).exportAsPng()
        # 发送回TG
        await check.check_photo(message, back_message, stime, nodenum, wtime)
    except RPCError as r:
        logger.error(r)
        await back_message.edit_message_text("出错啦")
    except KeyboardInterrupt:
        await message.reply("程序已被强行中止")
    except FloodWait as e:
        await asyncio.sleep(e.value)
