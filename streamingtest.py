import asyncio
import time
import async_timeout
from pyrogram.errors import RPCError, FloodWait
import re
import collector
import cleaner
import export
import proxys


async def testurl(client, message, back_message, test_members, start_time, suburl: str = None):
    print("当前序号:", test_members)
    progress = 0
    sending_time = 0
    if test_members > 4:
        await back_message.edit_text("⚠️测试任务数量达到最大，请等待一个任务完成。")
        return
    try:
        chat_id = message.chat.id
        info = {}  # Netflix Youtube 等等
        if suburl is not None:
            url = suburl
        else:
            text = str(message.text)
            pattern = re.compile(
                r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")  # 匹配订阅地址
            # 获取订阅地址
            try:
                url = pattern.findall(text)[0]  # 列表中第一个项为订阅地址
            except IndexError:
                await back_message.edit_text("⚠️无效的订阅地址，请检查后重试。")
                return
        print(url)
        # 启动订阅采集器
        sub = collector.SubCollector(suburl=url)
        config = await sub.getSubConfig(save_path='./clash/sub{}.yaml'.format(start_time))
        if not config:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=back_message.id,
                text="ERROR: 无法获取到订阅文件"
            )
            return

        # 启动订阅清洗
        with open('./clash/sub{}.yaml'.format(start_time), "r", encoding="UTF-8") as fp:
            cl = cleaner.ClashCleaner(fp)
            nodename = cl.nodesName()
            nodetype = cl.nodesType()
            nodenum = cl.nodesCount()
        # 检查获得的数据
        if nodename is None or nodenum is None or nodetype is None:
            await back_message.edit_text("❌发生错误，请检查订阅文件")
            return
        ma = cleaner.ConfigManager('./clash/proxy.yaml')
        ma.addsub(subname=start_time, subpath='./sub{}.yaml'.format(start_time))
        ma.save('./clash/proxy.yaml')
        proxy_group = 'auto'
        # 重载配置文件
        await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=1123)
        # 进入循环，直到所有任务完成
        ninfo = []  # 存放所测节点Netflix的解锁信息
        youtube_info = []
        disneyinfo = []
        rtt = []
        s1 = time.time()
        old_rtt = await collector.delay_providers(providername=start_time)
        if old_rtt == 0:
            rtt = [0 for _ in range(nodenum)]
        else:
            for r1 in old_rtt:
                rtt.append(str(r1))
        print(rtt)
        rtt_num = 0
        # 启动流媒体测试
        for n in nodename:
            if old_rtt[rtt_num] == 0:
                print("超时节点，跳过测试......")
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
        new_y = []
        info['类型'] = nodetype
        info['延迟RTT'] = rtt
        # 过滤None值
        for i in youtube_info:
            if i is None:
                a = "N/A"
                new_y.append(a)
            elif i == "A":
                new_y.append("N/A")
            else:
                new_y.append(i)
        info['Youtube'] = new_y
        new_n = []
        # 过滤None值
        for i in ninfo:
            if i is None:
                a = "N/A"
                new_n.append(a)
            else:
                new_n.append(i)
        info['Netflix'] = new_n
        # 过滤None值
        new_dis = []
        for d in disneyinfo:
            if d is None:
                new_dis.append("N/A")
            else:
                new_dis.append(d)
        info['Disney+'] = new_dis
        print(rtt)
        print(new_y)
        print(new_n)
        print(new_dis)
        info = cleaner.ResultCleaner(info).start()
        # 计算测试消耗时间
        wtime = "%.1f" % float(time.time() - s1)
        info['wtime'] = wtime
        # 生成图片
        # stime = export.exportImage(proxyname=nodename, info=info)
        stime = export.ExportResult(nodename=nodename, info=info).exportAsPng()
        # 发送回TG
        with async_timeout.timeout(30):
            if stime is None:
                await back_message.edit_text("⚠️生成图片失败,可能原因:节点名称包含国旗⚠️\n")
                new_stime = export.exportImage_old(proxyname=nodename, info=info)
                if new_stime is None:
                    await back_message.edit_text("⚠️生成图片失败!")
                else:
                    if len(nodename) > 50:
                        await message.reply_document(r"./results/{}.png".format(stime),
                                                     caption="⏱️总共耗时: {}s".format(wtime))
                    await message.reply_photo(r"./results/{}.png".format(stime),
                                              caption="⏱️总共耗时: {}s".format(wtime))
                    await back_message.delete()
                    await message.delete()
            else:
                if len(nodename) > 50:
                    await message.reply_document(r"./results/{}.png".format(stime),
                                                 caption="⏱️总共耗时: {}s".format(wtime))
                else:
                    await message.reply_photo(r"./results/{}.png".format(stime),
                                              caption="⏱️总共耗时: {}s".format(wtime))
                await back_message.delete()
                await message.delete()
    except RPCError as r:
        print(r)
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=back_message.id,
            text="出错啦"
        )
    except KeyboardInterrupt:
        await message.reply("程序已被强行中止")
    except FloodWait as e:
        await asyncio.sleep(e.value)  # Wait "value" seconds before continuing
