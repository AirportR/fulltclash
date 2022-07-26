import time
import async_timeout
from pyrogram.errors import RPCError
import re
import collector
import cleaner
import export
import proxys


async def testurl(client, message, back_message, test_members):
    global subp
    print("当前序号:", test_members)
    progress = 0
    if test_members > 4:
        await back_message.edit_text("⚠️测试任务数量达到最大，请等待一个任务完成。")
        return
    try:
        chat_id = message.chat.id
        text = str(message.text)

        pattern = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")  # 匹配订阅地址

        info = {}  # Netflix Youtube 等等
        # 获取订阅地址
        try:
            url = pattern.findall(text)[0]  # 列表中第一个项为订阅地址
        except IndexError:
            await back_message.edit_text("⚠️无效的订阅地址，请检查后重试。")
            return
        print(url)
        # 启动订阅采集器
        suburl = url
        sub = collector.SubCollector(suburl=suburl)
        sname = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
        config = await sub.getSubConfig(save_path='./clash/sub{}.yaml'.format(sname))
        if not config:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=back_message.id,
                text="ERROR: 无法获取到订阅文件"
            )
            return

        # 启动订阅清洗
        with open('./clash/sub{}.yaml'.format(sname), "r", encoding="UTF-8") as fp:
            cl = cleaner.ClashCleaner(fp)
            nodename = cl.nodesName()
            nodetype = cl.nodesType()
            nodenum = cl.nodesCount()
        ma = cleaner.ConfigManager('./clash/proxy.yaml')
        ma.addsub(subname=sname, subpath='./sub{}.yaml'.format(sname))
        ma.save('./clash/proxy.yaml')
        proxy_group = 'auto'
        # 重载配置文件
        await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=1123)
        ma.delsub(subname=sname)
        ma.save(savePath='./clash/proxy.yaml')
        # 进入循环，直到所有任务完成
        ninfo = []  # 存放所测节点Netflix的解锁信息
        youtube_info = []
        disneyinfo = []
        rtt = await collector.delay_providers(providername=sname)
        print(rtt)
        # 启动流媒体测试
        s1 = time.time()
        for n in nodename:
            proxys.switchProxy_old(proxyName=n, proxyGroup=proxy_group, clashPort=1123)
            progress += 1
            cl = collector.Collector()
            n1 = await cl.start(proxy="http://127.0.0.1:{}".format(1122))
            clean = cleaner.ReCleaner(n1)
            nf = clean.getnetflixinfo()
            if nf is None:
                print("发现空类型，已重新赋值")
                nf = ["N/A", "N/A", "N/A"]
            print("netflix:", nf)
            ninfo.append(nf[len(nf) - 1])
            you = clean.getyoutubeinfo()
            youtube_info.append(you)
            dis = clean.getDisneyinfo()
            disneyinfo.append(dis)
            p_text = "%.2f" % (progress / nodenum * 100)
            await back_message.edit_text("╰(*°▽°*)╯流媒体测试进行中...\n\n" +
                                         "当前进度:\n" + p_text +
                                         "%     [" + str(progress) + "/" + str(nodenum) + "]")  # 实时反馈进度
        netflix = ninfo
        new_y = []
        # 过滤None值
        for i in youtube_info:
            if i is None:
                a = "N/A"
                new_y.append(a)
            elif i == "A":
                new_y.append("N/A")
            else:
                new_y.append(i)
        info['youtube'] = new_y
        new_n = []
        # 过滤None值
        for i in netflix:
            if i is None:
                a = "N/A"
                new_n.append(a)
            elif i == "A":
                new_n.append("N/A")
            else:
                new_n.append(i)
        info['netflix'] = new_n
        # 过滤None值
        new_dis = []
        for d in disneyinfo:
            if d is None:
                new_dis.append("N/A")
            else:
                new_dis.append(d)
        info['disney'] = new_dis
        if rtt is None:
            rtt = []
            for i in range(nodenum):
                rtt.append(-1)
        info['delay'] = rtt
        print(rtt)
        print(new_y)
        print(new_n)
        print(new_dis)
        # 计算测试消耗时间
        wtime = "%.1f" % float(time.time() - s1)
        info['wtime'] = wtime
        # 生成图片
        stime = export.exportImage(proxyname=nodename, proxytype=nodetype, info=info)
        # 发送回TG
        with async_timeout.timeout(30):
            if stime is None:
                await back_message.edit_text("⚠️生成图片失败,可能原因:节点名称包含国旗⚠️\n尝试使用旧版方案......")
                new_stime = export.exportImage_old(proxyname=nodename, proxytype=nodetype, info=info)
                if new_stime is None:
                    await back_message.edit_text("⚠️生成图片失败!")
                else:
                    if len(nodename) > 60:
                        await message.reply_document(r"./results/result-{}.png".format(stime),
                                                     caption="⏱️总共耗时: {}s".format(wtime))
                    await message.reply_photo(r"./results/result-{}.png".format(new_stime),
                                              caption="⏱️总共耗时: {}s".format(wtime))
                    await back_message.delete()
                    await message.delete()
            else:
                if len(nodename) > 60:
                    await message.reply_document(r"./results/result-{}.png".format(stime),
                                                 caption="⏱️总共耗时: {}s".format(wtime))
                await message.reply_photo(r"./results/result-{}.png".format(stime),
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
        subp.kill()
