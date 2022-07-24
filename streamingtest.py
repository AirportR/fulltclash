import time
import subprocess

import async_timeout
from pyrogram.errors import RPCError
import re
import collector
import cleaner
import export
import proxys

# 你需要一个clash核心程序，此为clash核心运行路径。Windows需要加后缀名.exe
clash_path = "./clash-windows-amd64.exe"
sub_path = "./sub.yaml"
progress = 0  # 整个测试进程的进度
port = 1122


async def testurl(client, message, back_message):
    global subp, progress
    if progress != 0:
        await back_message.edit_text("⚠️当前已有测试任务运行，请等待上一个任务完成。")
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
        config = await sub.getSubConfig()
        if not config:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=back_message.id,
                text="ERROR: 无法获取到订阅文件"
            )
            return

        # 启动订阅清洗
        with open(sub_path, "r", encoding="UTF-8") as fp:
            cl = cleaner.ClashCleaner(fp)
            nodename = cl.nodesName()
            nodetype = cl.nodesType()
            nodenum = cl.nodesCount()
            cl.changeClashPort(port=port)
            cl.changeClashEC()
            # cl.changeClashMode()
            proxy_group = cl.proxyGroupName()
        cl.save()
        # 启动clash进程
        command = fr"{clash_path} -f {sub_path}"
        subp = subprocess.Popen(command.split(), encoding="utf-8")
        time.sleep(2)
        # 进入循环，直到所有任务完成
        ninfo = []  # 存放所测节点Netflix的解锁信息
        youtube_info = []
        disneyinfo = []
        gpinginfo = []
        # 启动流媒体测试
        s1 = time.time()
        for n in nodename:
            proxys.switchProxy_old(proxyName=n, proxyGroup=proxy_group)
            progress += 1
            cl = collector.Collector()
            n1 = await cl.start(proxy="http://127.0.0.1:{}".format(port))
            clean = cleaner.ReCleaner(n1)
            gp = clean.getGping()
            if gp is None:
                print("发现gping空类型，已重新赋值")
                gp = "0ms"
            gpinginfo.append(gp)
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
        # 关闭进程
        subp.kill()
        progress = 0
        print(gpinginfo)
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
        info['delay'] = gpinginfo
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
