from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
import time
# from pilmoji.source import MicrosoftEmojiSource


_version_ = "3.0(dev)"  # 版本号


# info 变量里面包含测好的解锁信息
def exportImage(proxyname: list, proxytype: list, info: dict):
    save_path = "./results"
    try:
        netflixinfo = info['netflix']
        youtubeinfo = info['youtube']
        disneyinfo = info['disney']
        gpinginfo = info['delay']
        # 加载字体文件
        size = 30  # 字号大小
        fnt = ImageFont.truetype(r"./resources/微软雅黑.ttf", size)  # 加载字体文件
        numNodes = len(proxyname)  # 节点数
        num1 = numNodes + 3  # 40为宽度,需要画的横线数量，线的数量等于 节点数 + 3
        max_ize = []
        # 计算偏移量
        for n in proxyname:
            max_ize.append(30 * len(n))
        if max(max_ize) <= 420:
            num2 = 0  # 偏移量,根据节点名称动态改变表格横向长度
        else:
            num2 = max(max_ize) - 420
        youtube_length = 150  # youtube条目宽度
        disdey_length = 150  # disney条目宽度
        image_width = 980 + youtube_length + disdey_length + num2  # 图片宽度
        out = Image.new("RGB", (image_width, (numNodes + 4) * 40), (255, 255, 255))  # 确定图片的长度，为节点数 + 4
        pilmoji = Pilmoji(out)  # emoji表情修复
        # 适用于Netflix 的填充块
        cg = Image.new('RGB', (130, 40), "#bee47e")  # 成功解锁的绿色填充块
        sb = Image.new('RGB', (130, 40), "#ee6b73")  # 解锁失败的红色填充块
        na = Image.new('RGB', (130, 40), "#8d8b8e")  # N/A 的灰色填充块
        # 适用于youtube、disney+的填充块
        cg2 = Image.new('RGB', (youtube_length, 40), "#bee47e")  # 成功解锁的绿色填充块
        sb2 = Image.new('RGB', (youtube_length, 40), "#ee6b73")  # 解锁失败的红色填充块
        na2 = Image.new('RGB', (youtube_length, 40), "#8d8b8e")  # N/A 的灰色填充块

        # 画画对象
        d = ImageDraw.Draw(out)
        # 第一行内容
        d.text((image_width / 2 - 120, 4), "FullTclash - 流媒体测试", font=fnt, fill=(0, 0, 0))
        # 表格项
        export_time1 = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())  # 文件动态命名,输出图片的时间
        list1 = ["序号", "节点名称", "类型", "延迟RTT", "Disney+", "Netflix", "Youtube",
                 "版本:{}     ⏱️总共耗时: {}s".format(_version_, info['wtime']),
                 "测试时间: {}  测试结果仅供参考,以实际情况为准".format(export_time1)]

        d.text((20, 40), text=list1[0], font=fnt, fill=(0, 0, 0))  # 序号
        d.text(((500 + num2 - 100) / 2 + 2 * size, 40), text=list1[1], font=fnt, fill=(0, 0, 0))  # 节点名称
        d.text((570 + num2, 40), text=list1[2], font=fnt, fill=(0, 0, 0))  # 类型
        d.text((720 + num2, 40), text=list1[3], font=fnt, fill=(0, 0, 0))  # 延迟RTT
        d.text((1150 + num2, 40), text=list1[4], font=fnt, fill=(0, 0, 0))  # Disney+
        d.text((870 + num2, 40), text=list1[5], font=fnt, fill=(0, 0, 0))  # Netflix
        d.text((1000 + num2, 40), text=list1[6], font=fnt, fill=(0, 0, 0))  # Youtube
        # d.text((20, 40 * (num1 - 1)), text=list1[7], font=fnt, fill=(0, 0, 0))  # 版本信息
        pilmoji.text((20, 40 * (num1 - 1)), text=list1[7], font=fnt, fill=(0, 0, 0))  # 版本信息
        d.text((20, 40 * num1), text=list1[8], font=fnt, fill=(0, 0, 0))  # 测试时间

        # 打印信息
        l1 = int((image_width + 1130 + num2) / 2 - 30)  # Disney+解锁文字放入的位置，为两条竖线的中间 减 一个字的距离
        for t in range(numNodes):
            if netflixinfo[t] == "解锁":
                out.paste(cg, (850 + num2, 40 * (t + 2)))
            elif netflixinfo[t] == "失败":
                out.paste(sb, (850 + num2, 40 * (t + 2)))
            elif netflixinfo[t] == "N/A":
                out.paste(na, (850 + num2, 40 * (t + 2)))
            d.text((40, 40 * (t + 2)), text=str(t + 1), font=fnt, fill=(0, 0, 0))  # 序号
            # d.text((110, 40 * (t + 2)), text=proxyname[t], font=fnt, fill=(0, 0, 0))  # 节点名称
            pilmoji.text((110, 40 * (t + 2)), text=proxyname[t], font=fnt, fill=(0, 0, 0))
            if proxytype[t] == "ss":
                d.text((510 + num2, 40 * (t + 2)), text="Shadowsocks", font=fnt, fill=(0, 0, 0))  # 类型
            elif proxytype[t] == "trojan":
                d.text((510 + num2, 40 * (t + 2)), text="Trojan", font=fnt, fill=(0, 0, 0))  # 类型
            else:
                d.text((510 + num2, 40 * (t + 2)), text=proxytype[t], font=fnt, fill=(0, 0, 0))
            if netflixinfo[t] == "仅自制剧":
                d.text((855 + num2, 40 * (t + 2)), text=netflixinfo[t], font=fnt, fill=(0, 0, 0))  # netflix解锁
            else:
                d.text((880 + num2, 40 * (t + 2)), text=netflixinfo[t], font=fnt, fill=(0, 0, 0))  # netflix解锁
            # 延迟RTT
            d.text((730 + num2, 40 * (t + 2)), text=str(gpinginfo[t])+'ms', font=fnt, fill=(0, 0, 0))
            # Disney+
            if disneyinfo[t] == "解锁":
                out.paste(cg2, (1130 + num2, 40 * (t + 2)))
            elif disneyinfo[t] == "失败":
                out.paste(sb2, (1130 + num2, 40 * (t + 2)))
            else:
                out.paste(na2, (1130 + num2, 40 * (t + 2)))
            d.text((l1, 40 * (t + 2)), text=disneyinfo[t], font=fnt, fill=(0, 0, 0))  # Disney+解锁
            # Youtube
            if youtubeinfo[t] == "解锁":
                out.paste(cg2, (980 + num2, 40 * (t + 2)))
            elif youtubeinfo[t] == "失败":
                out.paste(sb2, (980 + num2, 40 * (t + 2)))
            else:
                out.paste(na2, (980 + num2, 40 * (t + 2)))
            d.text((1025 + num2, 40 * (t + 2)), text=youtubeinfo[t], font=fnt, fill=(0, 0, 0))  # youtube解锁
        # 画横线
        for t in range(num1):
            d.line([(0, 40 * (t + 1)), (image_width, 40 * (t + 1))], fill="#e1e1e1")
        # 画竖线
        d.line([(100, 40), (100, 80)], fill="#e1e1e1", width=1)  # 节点名称
        d.line([(500 + num2, 40), (500 + num2, 80)], fill="#e1e1e1", width=1)  # 类型
        d.line([(700 + num2, 40), (700 + num2, 80)], fill="#e1e1e1", width=1)  # 延迟RTT
        d.line([(850 + num2, 40), (850 + num2, 40 * (num1 - 1))], fill="#e1e1e1", width=1)  # 奈飞
        d.line([(980 + num2, 40), (980 + num2, 40 * (num1 - 1))], fill="#e1e1e1", width=1)  # Youtube
        d.line([(1130 + num2, 40), (1130 + num2, 40 * (num1 - 1))], fill="#e1e1e1", width=1)  # Disney+
        d.line([(image_width, 40), (image_width, 40 * (num1 - 1))], fill="#e1e1e1", width=1)  # 待定测试项
        # out.show()
        print(export_time1)
        out.save(r"./results/result-{}.png".format(export_time1))
        return export_time1
    except Exception as e:
        print(e)


def exportImage_old(proxyname: list, proxytype: list, info: dict):
    try:
        netflixinfo = info['netflix']
        youtubeinfo = info['youtube']
        disneyinfo = info['disney']
        gpinginfo = info['delay']
        # 加载字体文件
        size = 30  # 字号大小
        fnt = ImageFont.truetype(r"./resources/微软雅黑.ttf", size)  # 加载字体文件
        numNodes = len(proxyname)  # 节点数
        num1 = numNodes + 3  # 40为宽度,需要画的横线数量，线的数量等于 节点数 + 3
        max_ize = []
        # 计算偏移量
        for n in proxyname:
            max_ize.append(30 * len(n))
        if max(max_ize) <= 420:
            num2 = 0  # 偏移量,根据节点名称动态改变表格横向长度
        else:
            num2 = max(max_ize) - 420
        youtube_length = 150  # youtube条目宽度
        disdey_length = 150  # disney条目宽度
        image_width = 980 + youtube_length + disdey_length + num2  # 图片宽度
        out = Image.new("RGB", (image_width, (numNodes + 4) * 40), (255, 255, 255))  # 确定图片的长度，为节点数 + 4
        # pilmoji = Pilmoji(out, source=MicrosoftEmojiSource)  # emoji表情修复
        # 适用于Netflix 的填充块
        cg = Image.new('RGB', (130, 40), "#bee47e")  # 成功解锁的绿色填充块
        sb = Image.new('RGB', (130, 40), "#ee6b73")  # 解锁失败的红色填充块
        na = Image.new('RGB', (130, 40), "#8d8b8e")  # N/A 的灰色填充块
        # 适用于youtube、disney+的填充块
        cg2 = Image.new('RGB', (youtube_length, 40), "#bee47e")  # 成功解锁的绿色填充块
        sb2 = Image.new('RGB', (youtube_length, 40), "#ee6b73")  # 解锁失败的红色填充块
        na2 = Image.new('RGB', (youtube_length, 40), "#8d8b8e")  # N/A 的灰色填充块

        # 画画对象
        d = ImageDraw.Draw(out)
        # 第一行内容
        d.text((image_width / 2 - 120, 4), "掌柜的流媒体测试", font=fnt, fill=(0, 0, 0))
        # 表格项
        export_time1 = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())  # 文件动态命名
        list1 = ["序号", "节点名称", "类型", "HTTPing", "Disney+", "Netflix",
                 "Youtube", "版本:{}     ⏱️总共耗时: {}s".format(_version_, info['wtime']),
                 "测试时间: {}  测试结果仅供参考,以实际情况为准".format(export_time1)]

        d.text((20, 40), text=list1[0], font=fnt, fill=(0, 0, 0))  # 序号
        d.text(((500 + num2 - 100) / 2 + 2 * size, 40), text=list1[1], font=fnt, fill=(0, 0, 0))  # 节点名称
        d.text((570 + num2, 40), text=list1[2], font=fnt, fill=(0, 0, 0))  # 类型
        d.text((720 + num2, 40), text=list1[3], font=fnt, fill=(0, 0, 0))  # 延迟RTT
        d.text((1150 + num2, 40), text=list1[4], font=fnt, fill=(0, 0, 0))  # Disney+
        d.text((870 + num2, 40), text=list1[5], font=fnt, fill=(0, 0, 0))  # Netflix
        d.text((1000 + num2, 40), text=list1[6], font=fnt, fill=(0, 0, 0))  # Youtube
        d.text((20, 40 * (num1 - 1)), text=list1[7], font=fnt, fill=(0, 0, 0))  # 版本信息
        d.text((20, 40 * num1), text=list1[8], font=fnt, fill=(0, 0, 0))  # 测试时间

        # 打印信息
        l1 = int((image_width + 1130 + num2) / 2 - 30)  # Disney+解锁文字放入的位置，为两条竖线的中间 减 一个字的距离
        for t in range(numNodes):
            if netflixinfo[t] == "解锁":
                out.paste(cg, (850 + num2, 40 * (t + 2)))
            elif netflixinfo[t] == "失败":
                out.paste(sb, (850 + num2, 40 * (t + 2)))
            elif netflixinfo[t] == "N/A":
                out.paste(na, (850 + num2, 40 * (t + 2)))
            d.text((40, 40 * (t + 2)), text=str(t + 1), font=fnt, fill=(0, 0, 0))  # 序号
            d.text((110, 40 * (t + 2)), text=proxyname[t], font=fnt, fill=(0, 0, 0))  # 节点名称
            # pilmoji.text((110, 40 * (t + 2)), text=proxyname[t], font=fnt, fill=(0, 0, 0))
            if proxytype[t] == "ss":
                d.text((510 + num2, 40 * (t + 2)), text="Shadowsocks", font=fnt, fill=(0, 0, 0))  # 类型
            elif proxytype[t] == "trojan":
                d.text((510 + num2, 40 * (t + 2)), text="Trojan", font=fnt, fill=(0, 0, 0))  # 类型
            else:
                d.text((510 + num2, 40 * (t + 2)), text=proxytype[t], font=fnt, fill=(0, 0, 0))
            if netflixinfo[t] == "仅自制剧":
                d.text((855 + num2, 40 * (t + 2)), text=netflixinfo[t], font=fnt, fill=(0, 0, 0))  # netflix解锁
            else:
                d.text((880 + num2, 40 * (t + 2)), text=netflixinfo[t], font=fnt, fill=(0, 0, 0))  # netflix解锁
            # 延迟RTT
            d.text((730 + num2, 40 * (t + 2)), text=gpinginfo[t], font=fnt, fill=(0, 0, 0))  # netflix解锁
            # Disney+
            if disneyinfo[t] == "解锁":
                out.paste(cg2, (1130 + num2, 40 * (t + 2)))
            elif disneyinfo[t] == "失败":
                out.paste(sb2, (1130 + num2, 40 * (t + 2)))
            else:
                out.paste(na2, (1130 + num2, 40 * (t + 2)))
            d.text((l1, 40 * (t + 2)), text=disneyinfo[t], font=fnt, fill=(0, 0, 0))  # Disney+解锁
            # Youtube
            if youtubeinfo[t] == "解锁":
                out.paste(cg2, (980 + num2, 40 * (t + 2)))
            elif youtubeinfo[t] == "失败":
                out.paste(sb2, (980 + num2, 40 * (t + 2)))
            else:
                out.paste(na2, (980 + num2, 40 * (t + 2)))
            d.text((1025 + num2, 40 * (t + 2)), text=youtubeinfo[t], font=fnt, fill=(0, 0, 0))  # youtube解锁
        # 画横线
        for t in range(num1):
            d.line([(0, 40 * (t + 1)), (image_width, 40 * (t + 1))], fill="#e1e1e1")
        # 画竖线
        d.line([(100, 40), (100, 80)], fill="#e1e1e1", width=1)  # 节点名称
        d.line([(500 + num2, 40), (500 + num2, 80)], fill="#e1e1e1", width=1)  # 类型
        d.line([(700 + num2, 40), (700 + num2, 80)], fill="#e1e1e1", width=1)  # 延迟RTT
        d.line([(850 + num2, 40), (850 + num2, 40 * (num1 - 1))], fill="#e1e1e1", width=1)  # 奈飞
        d.line([(980 + num2, 40), (980 + num2, 40 * (num1 - 1))], fill="#e1e1e1", width=1)  # Youtube
        d.line([(1130 + num2, 40), (1130 + num2, 40 * (num1 - 1))], fill="#e1e1e1", width=1)  # Disney+
        d.line([(image_width, 40), (image_width, 40 * (num1 - 1))], fill="#e1e1e1", width=1)  # 待定测试项
        # out.show()
        print(export_time1)
        out.save(r"./results/result-{}.png".format(export_time1))
        return export_time1
    except Exception as e:
        print(e)
