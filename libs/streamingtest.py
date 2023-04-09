import asyncio
import time

from pyrogram.errors import RPCError, FloodWait
from loguru import logger
from utils import check, cleaner, collector, proxys
from utils.cleaner import config

"""
这个模块是流媒体测试的具体实现
"""


async def new_unit(test_items: list, delay: int, host="127.0.0.1", port=1122):
    """
    以一个节点的所有测试项为一个基本单元unit,返回单个节点的测试结果
    :param port: 代理端口
    :param host: 代理主机名
    :param test_items: [Netflix,disney+,etc...]
    :param delay: 节点延迟，可选参数，若为0，则测试项全部返回N/A
    :return: list 返回test_items对应顺序的信息
    """
    info = []
    if delay == 0:
        logger.warning("超时节点，跳过测试")
        for t in test_items:
            if t == "HTTP延迟":
                info.append(0)
            else:
                info.append("N/A")
        return info
    else:
        info.append(delay)
        cl = collector.Collector()
        re1 = await cl.start(host, port)
        cnr = cleaner.ReCleaner(re1)
        old_info = cnr.get_all()
        for item in test_items:
            i = item
            if i == 'HTTP延迟':
                continue
            try:
                info.append(old_info[i])
            except KeyError:
                info.append("N/A")
                logger.error("KeyError: 无法找到 " + item + " 测试项")
        return info


async def unit(test_items: list, delay: int, host="127.0.0.1", port=1122):
    """
    以一个节点的所有测试项为一个基本单元unit,返回单个节点的测试结果
    :param port: 代理端口
    :param host: 代理主机名
    :param test_items: [Netflix,disney+,etc...]
    :param delay: 节点延迟，可选参数，若为0，则测试项全部返回N/A
    :return: list 返回test_items对应顺序的信息
    """
    info = []
    if delay == 0:
        logger.warning("超时节点，跳过测试")
        for t in test_items:
            if t == "HTTP延迟":
                info.append(0)
            else:
                info.append("N/A")
        return info
    else:
        info.append(delay)
        cl = collector.Collector()
        re1 = await cl.start(host, port)
        cnr = cleaner.ReCleaner(re1)
        old_info = cnr.get_all()
        for item in test_items:
            i = item
            if i == 'HTTP延迟':
                continue
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


async def new_batch_test(message, nodename: list, delays: list, test_items: list, pool: dict, proxygroup='auto'):
    info = {}
    progress = 0
    sending_time = 0
    scripttext = config.config.get('bot', {}).get('scripttext', "⏳联通性测试进行中...")
    host = pool.get('host', [])
    port = pool.get('port', [])
    psize = len(port)
    nodenum = len(nodename)
    tasks = []
    for item in test_items:
        info[item] = []
    logger.info("接受任务数量: {} 线程数: {}".format(nodenum, psize))
    if psize <= 0:
        logger.error("无可用的代理程序接口")
        return {}
    await check.progress(message, 0, nodenum, 0, scripttext)
    if nodenum < psize:
        for i in range(len(port[:nodenum])):
            proxys.switchProxy(nodename[i], i)
            task = asyncio.create_task(unit(test_items, delays[i], host=host[i], port=port[i]))
            tasks.append(task)
        done = await asyncio.gather(*tasks)

        # 简单处理一下数据
        res = []
        for j in range(len(test_items)):
            res.clear()
            for d in done:
                res.append(d[j])
            info[test_items[j]].extend(res)
        logger.info(str(info))
        return info
    else:
        subbatch = nodenum // psize

        for s in range(subbatch):
            logger.info("当前批次: " + str(s + 1))
            tasks.clear()
            for i in range(psize):
                proxys.switchProxy(nodename[s * psize + i], i)
                task = asyncio.create_task(unit(test_items, delays[s * psize + i], host=host[i], port=port[i]))
                tasks.append(task)
            done = await asyncio.gather(*tasks)

            # 反馈进度

            progress += psize
            cal = progress / nodenum * 100
            # 判断进度条，每隔10%发送一次反馈，有效防止洪水等待(FloodWait)
            if cal > sending_time:
                await check.progress(message, progress, nodenum, cal, scripttext)
                sending_time += 20
            # 简单处理一下数据
            res = []
            for j in range(len(test_items)):
                res.clear()
                for d in done:
                    res.append(d[j])
                info[test_items[j]].extend(res)

        if nodenum % psize != 0:
            tasks.clear()
            logger.info("最后批次: " + str(subbatch + 1))
            for i in range(nodenum % psize):
                proxys.switchProxy(nodename[subbatch * psize + i], i)
                task = asyncio.create_task(unit(test_items, delays[subbatch * psize + i], host=host[i], port=port[i]))
                tasks.append(task)
            done = await asyncio.gather(*tasks)

            res = []
            for j in range(len(test_items)):
                res.clear()
                for d in done:
                    res.append(d[j])
                info[test_items[j]].extend(res)
        # 最终进度条
        if nodenum % psize != 0:
            await check.progress(message, nodenum, nodenum, 100, scripttext)
        logger.info(str(info))
        return info


@logger.catch()
async def batch_test_pro(message, nodename: list, delays: list, test_items: list, pool: dict, proxygroup='auto'):
    info = {}
    progress = 0
    sending_time = 0
    scripttext = config.config.get('bot', {}).get('scripttext', "⏳联通性测试进行中...")
    host = pool.get('host', [])
    port = pool.get('port', [])
    psize = len(port)
    nodenum = len(nodename)
    tasks = []
    for item in test_items:
        info[item] = []
    logger.info("接受任务数量: {} 线程数: {}".format(nodenum, psize))
    if psize <= 0:
        logger.error("无可用的代理程序接口")
        return {}
    bar = '  ' *  16
    bar_with_frame = '[{}]'.format(bar)
    await check.progress(message, 0, nodenum, 0, scripttext + '\n' + '\n' + bar_with_frame)
    if nodenum < psize:
        for i in range(len(port[:nodenum])):
            proxys.switchProxy_old(proxyName=nodename[i], proxyGroup=proxygroup, clashHost=host[i],
                                   clashPort=port[i] + 1)
            task = asyncio.create_task(unit(test_items, delays[i], host=host[i], port=port[i]))
            tasks.append(task)
        done = await asyncio.gather(*tasks)

        # 简单处理一下数据
        res = []
        for j in range(len(test_items)):
            res.clear()
            for d in done:
                res.append(d[j])
            info[test_items[j]].extend(res)
        logger.info(str(info))
        return info
    else:
        subbatch = nodenum // psize

        for s in range(subbatch):
            logger.info("当前批次: " + str(s + 1))
            tasks.clear()
            for i in range(psize):
                proxys.switchProxy_old(proxyName=nodename[s * psize + i], proxyGroup=proxygroup, clashHost=host[i],
                                       clashPort=port[i] + 1)

                task = asyncio.create_task(unit(test_items, delays[s * psize + i], host=host[i], port=port[i]))
                tasks.append(task)
            done = await asyncio.gather(*tasks)

            # 反馈进度

            progress += psize
            cal = progress / nodenum
            bar_length = 50
            num_eq = int(cal * bar_length)
            num_space = bar_length - num_eq
            # 判断进度条，每隔10%发送一次反馈，有效防止洪水等待(FloodWait)
            if cal * 100 >= sending_time:
                eq_ratio = int(cal * 100 / 2)
                eq = '=' * (1 + num_eq * eq_ratio // 100)
                space = ' ' * num_space
                bar = eq + space
                bar_with_frame = '[{}]'.format(bar)
                await check.progress(message, progress, nodenum, cal * 100, scripttext + '\n' + '\n' + bar_with_frame)
                sending_time += 20
            # 简单处理一下数据
            res = []
            for j in range(len(test_items)):
                res.clear()
                for d in done:
                    res.append(d[j])
                info[test_items[j]].extend(res)

        if nodenum % psize != 0:
            tasks.clear()
            logger.info("最后批次: " + str(subbatch + 1))
            for i in range(nodenum % psize):
                proxys.switchProxy_old(proxyName=nodename[subbatch * psize + i], proxyGroup=proxygroup,
                                       clashHost=host[i],
                                       clashPort=port[i] + 1)
                task = asyncio.create_task(unit(test_items, delays[subbatch * psize + i], host=host[i], port=port[i]))
                tasks.append(task)
            done = await asyncio.gather(*tasks)

            res = []
            for j in range(len(test_items)):
                res.clear()
                for d in done:
                    res.append(d[j])
                info[test_items[j]].extend(res)
        # 最终进度条
        cal = progress / nodenum
        bar_length = 27
        num_eq = int(cal * bar_length)
        num_space = bar_length - num_eq
        if nodenum % psize != 0:
            bar = '=' * num_eq
            bar_with_frame = '[{}]'.format(bar)
            await check.progress(message, nodenum, nodenum, 100, scripttext + '\n' + '\n' + bar_with_frame)
        logger.info(str(info))
        return info


async def newcore(message, back_message, start_time, suburl: str = None, media_items: list = None, thread: int = 1,
                  **kwargs):
    info = {}  # 存放Netflix Youtube 等等
    include_text = ''
    exclude_text = ''
    if media_items is None:
        test_items = collector.media_items
    else:
        test_items = media_items
    if suburl is not None:
        url = suburl
        text = str(message.text)
        texts = text.split(' ')
        if len(texts) > 2:
            include_text = texts[2]
        if len(texts) > 3:
            exclude_text = texts[3]
        if kwargs.get('include_text', ''):
            include_text = kwargs.get('include_text', '')
        if kwargs.get('exclude_text', ''):
            exclude_text = kwargs.get('exclude_text', '')
    else:
        text = str(message.text)
        texts = text.split(' ')
        if len(texts) > 2:
            include_text = texts[2]
        if len(texts) > 3:
            exclude_text = texts[3]
        url = cleaner.geturl(text)
    if await check.check_url(back_message, url):
        return info
    startup = cleaner.config.config.get('clash', {}).get('startup', 1124)
    pool = {'host': ['127.0.0.1' for _ in range(thread)],
            'port': [startup + t * 2 for t in range(thread)]}
    print(url)
    # 订阅采集
    logger.info(f"过滤器: 包含: [{include_text}], 排除: [{exclude_text}]")
    sub = collector.SubCollector(suburl=url, include=include_text, exclude=exclude_text)
    subconfig = await sub.getSubConfig(save_path='./clash/sub{}.yaml'.format(start_time))
    if await check.check_sub(back_message, subconfig):
        return info
    try:
        # 启动订阅清洗
        cl = cleaner.ClashCleaner(f'./clash/sub{start_time}.yaml')
        cl.node_filter(include_text, exclude_text)
        nodename = cl.nodesName()
        nodelist = cl.getProxies()
        nodetype = cl.nodesType()
        nodenum = cl.nodesCount()
    except Exception as e:
        logger.error(e)
        nodelist = None
        nodename = None
        nodetype = None
        nodenum = None
    # 检查获得的数据
    if await check.check_nodes(back_message, nodenum, (nodename, nodetype,)):
        return info
    ma = cleaner.ConfigManager(':memory:')
    ma.addsub2provider(subname=start_time, subpath='./sub{}.yaml'.format(start_time))
    ma.save('./clash/proxy.yaml')
    # 重载配置文件
    # if not await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=1123):
    #     return info
    # try:
    #     if nodenum < len(pool.get('port', [])):
    #         for i in pool.get('port', [])[:nodenum]:
    #             if not await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=i + 1):
    #                 return info
    #     else:
    #         for i in pool.get('port', []):
    #             if not await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=i + 1):
    #                 return info
    # except Exception as e:
    #     logger.error(str(e))
    #     return info
    logger.info("开始测试延迟...")
    await back_message.edit_text(f"正在测试延迟... \n\n{nodenum}个节点")
    s1 = time.time()
    # old_rtt = await collector.delay_providers(providername=start_time)
    # rtt1 = check.check_rtt(old_rtt, nodenum)
    # print("第一次延迟:", rtt1)
    # old_rtt = await collector.delay_providers(providername=start_time)
    # rtt2 = check.check_rtt(old_rtt, nodenum)
    # print("第二次延迟:", rtt2)
    # old_rtt = await collector.delay_providers(providername=start_time)
    # rtt3 = check.check_rtt(old_rtt, nodenum)
    # print("第三次延迟:", rtt3)
    # rtt = cleaner.ResultCleaner.get_http_latency([rtt1, rtt2, rtt3])
    rtt = [100+i*20 for i in range(nodenum)]
    # 启动流媒体测试
    try:
        info['节点名称'] = nodename
        info['类型'] = nodetype
        test_info = await new_batch_test(back_message, nodelist, rtt, test_items, pool)
        info['HTTP延迟'] = test_info.pop('HTTP延迟')
        # info['HTTP延迟(内核)'] = rtt
        info.update(test_info)
        sort = kwargs.get('sort', "订阅原序")
        logger.info("排序：" + sort)
        info = cleaner.ResultCleaner(info).start(sort=sort)
        # 计算测试消耗时间
        wtime = "%.1f" % float(time.time() - s1)
        info['wtime'] = wtime
        info['sort'] = sort
        # 过滤器内容
        info['filter'] = {'include': include_text, 'exclude': exclude_text}
        # 保存结果
        cl1 = cleaner.ConfigManager(configpath=r"./results/{}.yaml".format(start_time.replace(':', '-')), data=info)
        cl1.save(r"./results/{}.yaml".format(start_time.replace(':', '-')))
    except RPCError as r:
        logger.error(r)
        await back_message.edit_text("出错啦")
    except FloodWait as e:
        logger.error(str(e))
        await asyncio.sleep(e.value)
    finally:
        return info


@logger.catch()
async def core(message, back_message, start_time, suburl: str = None, media_items: list = None, thread: int = 1,
               **kwargs):
    """
    :param thread: 测试线程
    :param message: 发起测试任务的对象
    :param back_message: 回复的消息对象
    :param start_time: 任务生成时间，取名用的
    :param suburl: 订阅地址,没有则尝试从配置文件匹配
    :param media_items: 测试的流媒体选项
    :return:
    """
    info = {}  # 存放Netflix Youtube 等等
    include_text = ''
    exclude_text = ''
    if media_items is None:
        test_items = collector.media_items
    else:
        test_items = media_items
    if suburl is not None:
        url = suburl
        text = str(message.text)
        texts = text.split(' ')
        if len(texts) > 2:
            include_text = texts[2]
        if len(texts) > 3:
            exclude_text = texts[3]
        if kwargs.get('include_text', ''):
            include_text = kwargs.get('include_text', '')
        if kwargs.get('exclude_text', ''):
            exclude_text = kwargs.get('exclude_text', '')
    else:
        text = str(message.text)
        texts = text.split(' ')
        if len(texts) > 2:
            include_text = texts[2]
        if len(texts) > 3:
            exclude_text = texts[3]
        url = cleaner.geturl(text)
    if await check.check_url(back_message, url):
        return info
    startup = cleaner.config.config.get('clash', {}).get('startup', 1124)
    pool = {'host': ['127.0.0.1' for _ in range(thread)],
            'port': [startup + t * 2 for t in range(thread)]}
    print(url)
    # 订阅采集
    logger.info(f"过滤器: 包含: [{include_text}], 排除: [{exclude_text}]")
    sub = collector.SubCollector(suburl=url, include=include_text, exclude=exclude_text)
    subconfig = await sub.getSubConfig(save_path='./clash/sub{}.yaml'.format(start_time))
    if await check.check_sub(back_message, subconfig):
        return info
    try:
        # 启动订阅清洗
        cl = cleaner.ClashCleaner(f'./clash/sub{start_time}.yaml')
        cl.node_filter(include_text, exclude_text)
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
        return info
    ma = cleaner.ConfigManager(':memory:')
    ma.addsub2provider(subname=start_time, subpath='./sub{}.yaml'.format(start_time))
    ma.save('./clash/proxy.yaml')
    # 重载配置文件
    if not await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=1123):
        return info
    try:
        if nodenum < len(pool.get('port', [])):
            for i in pool.get('port', [])[:nodenum]:
                if not await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=i + 1):
                    return info
        else:
            for i in pool.get('port', []):
                if not await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=i + 1):
                    return info
    except Exception as e:
        logger.error(str(e))
        return info
    logger.info("开始测试延迟...")
    await back_message.edit_text(f"正在测试延迟... \n\n{nodenum}个节点")
    s1 = time.time()
    old_rtt = await collector.delay_providers(providername=start_time)
    rtt1 = check.check_rtt(old_rtt, nodenum)
    print("第一次延迟:", rtt1)
    old_rtt = await collector.delay_providers(providername=start_time)
    rtt2 = check.check_rtt(old_rtt, nodenum)
    print("第二次延迟:", rtt2)
    old_rtt = await collector.delay_providers(providername=start_time)
    rtt3 = check.check_rtt(old_rtt, nodenum)
    print("第三次延迟:", rtt3)
    rtt = cleaner.ResultCleaner.get_http_latency([rtt1, rtt2, rtt3])
    # 启动流媒体测试
    try:
        info['节点名称'] = nodename
        info['类型'] = nodetype
        test_info = await batch_test_pro(back_message, nodename, rtt, test_items, pool)
        info['HTTP延迟'] = test_info.pop('HTTP延迟')
        # info['HTTP延迟(内核)'] = rtt
        info.update(test_info)
        sort = kwargs.get('sort', "订阅原序")
        logger.info("排序：" + sort)
        info = cleaner.ResultCleaner(info).start(sort=sort)
        # 计算测试消耗时间
        wtime = "%.1f" % float(time.time() - s1)
        info['wtime'] = wtime
        info['sort'] = sort
        # 过滤器内容
        info['filter'] = {'include': include_text, 'exclude': exclude_text}
        # 保存结果
        cl1 = cleaner.ConfigManager(configpath=r"./results/{}.yaml".format(start_time.replace(':', '-')), data=info)
        cl1.save(r"./results/{}.yaml".format(start_time.replace(':', '-')))
    except RPCError as r:
        logger.error(r)
        await back_message.edit_text("出错啦")
    except FloodWait as e:
        logger.error(str(e))
        await asyncio.sleep(e.value)
    finally:
        return info


if __name__ == "__main__":
    print("this is a demo")
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)


    async def test():
        pass


    loop.run_until_complete(test())
