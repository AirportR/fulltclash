import asyncio
import time

from pyrogram.errors import RPCError, FloodWait
from loguru import logger
from libs import cleaner, collector, proxys, check

"""
这个模块是流媒体测试的具体实现
"""


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
    delay2 = await collector.delay_https_task(proxy=f"http://{host}:{port}", times=3)
    if delay == 0 and delay2 == '0ms':
        for t in test_items:
            if t == "HTTP延迟":
                info.append("0ms")
            else:
                info.append("N/A")
        return info
    else:
        info.append(delay2)
        cl = collector.Collector()
        re1 = await cl.start(proxy=f"http://{host}:{port}")
        cnr = cleaner.ReCleaner(re1)
        old_info = cnr.get_all()
        for item in test_items:
            i = item.capitalize() if item != "BBC" and item != "HTTP延迟" else item
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


@logger.catch()
async def batch_test_pro(message, nodename: list, delays: list, test_items: list, pool: dict, proxygroup='auto'):
    info = {}
    progress = 0
    sending_time = 0
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
    await check.progress(message, 0, nodenum, 0, "╰(*°▽°*)╯联通性测试进行中...")
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
            cal = progress / nodenum * 100
            # 判断进度条，每隔10%发送一次反馈，有效防止洪水等待(FloodWait)
            if cal > sending_time:
                await check.progress(message, progress, nodenum, cal, "╰(*°▽°*)╯联通性测试进行中...")
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
        if nodenum % psize != 0:
            await check.progress(message, nodenum, nodenum, 100, "╰(*°▽°*)╯联通性测试进行中...")
        logger.info(str(info))
        return info


@logger.catch()
async def core(message, back_message, start_time, suburl: str = None, media_items: list = None, thread: int = 1, **kwargs):
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
    pool = {'host': ['127.0.0.1' for _ in range(thread)],
            'port': [1124 + t * 2 for t in range(thread)]}
    print(url)
    # 订阅采集
    logger.info(f"过滤器: 包含: [{include_text}], 排除: [{exclude_text}]")
    sub = collector.SubCollector(suburl=url, include=include_text, exclude=exclude_text)
    subconfig = await sub.getSubConfig(save_path='./clash/sub{}.yaml'.format(start_time))
    if await check.check_sub(back_message, subconfig):
        return info
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    ma.addsub2provider(subname=start_time, subpath='./sub{}.yaml'.format(start_time))
    ma.save('./clash/proxy.yaml')
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
        return info
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
    rtt = check.check_rtt(old_rtt, nodenum)
    print("延迟:", rtt)
    # 启动流媒体测试
    try:
        info['节点名称'] = nodename
        info['类型'] = nodetype
        # info['延迟RTT'] = rtt
        test_info = await batch_test_pro(back_message, nodename, rtt, test_items, pool)
        info.update(test_info)
        info = cleaner.ResultCleaner(info).start()
        # 计算测试消耗时间
        wtime = "%.1f" % float(time.time() - s1)
        info['wtime'] = wtime
        # 过滤器内容
        info['filter'] = {'include': include_text, 'exclude': exclude_text}
        # 保存结果
        cl1 = cleaner.ConfigManager(configpath=r"./results/{}.yaml".format(start_time.replace(':', '-')), data=info)
        cl1.save(r"./results/{}.yaml".format(start_time.replace(':', '-')))
    except RPCError as r:
        logger.error(r)
        await back_message.edit_text("出错啦")
    except KeyboardInterrupt:
        await message.reply("程序已被强行中止")
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
