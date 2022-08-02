from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
import time

# from pilmoji.source import MicrosoftEmojiSource


__version__ = "3.0.2(dev)"  # 版本号


# info 变量里面包含测好的解锁信息
def exportImage(proxyname: list, info: dict):
    save_path = "./results"
    try:
        netflixinfo = info['netflix']
        youtubeinfo = info['youtube']
        disneyinfo = info['disney']
        gpinginfo = info['delay']
        proxytype = info['type']
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
        djs2 = Image.new('RGB', (youtube_length, 40), "#dcc7e1")  # 待解锁的填充块
        na2 = Image.new('RGB', (youtube_length, 40), "#8d8b8e")  # N/A 的灰色填充块

        # 画画对象
        d = ImageDraw.Draw(out)
        # 第一行内容
        d.text((image_width / 2 - 120, 4), "FullTclash - 流媒体测试", font=fnt, fill=(0, 0, 0))
        # 表格项
        export_time1 = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())  # 文件动态命名,输出图片的时间
        list1 = ["序号", "节点名称", "类型", "延迟RTT", "Disney+", "Netflix", "Youtube",
                 "版本:{}     ⏱️总共耗时: {}s".format(__version__, info['wtime']),
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
        l1 = int((image_width + 1130 + num2) / 2 - 60)  # Disney+解锁文字放入的位置，为两条竖线的中间 减 一个字的距离
        for t in range(numNodes):
            if "解锁" in netflixinfo[t]:
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
            elif proxytype[t] == "vmess":
                d.text((510 + num2, 40 * (t + 2)), text="Vmess", font=fnt, fill=(0, 0, 0))  # 类型
            else:
                d.text((510 + num2, 40 * (t + 2)), text=proxytype[t].capitalize(), font=fnt, fill=(0, 0, 0))
            if netflixinfo[t] == "仅自制剧":
                d.text((855 + num2, 40 * (t + 2)), text=netflixinfo[t], font=fnt, fill=(0, 0, 0))  # netflix解锁
            else:
                d.text((880 + num2, 40 * (t + 2)), text=netflixinfo[t], font=fnt, fill=(0, 0, 0))  # netflix解锁
            # 延迟RTT
            d.text((730 + num2, 40 * (t + 2)), text=str(gpinginfo[t]) + 'ms', font=fnt, fill=(0, 0, 0))
            # Disney+
            if "解锁" in disneyinfo[t] and '待' not in disneyinfo[t]:
                out.paste(cg2, (1130 + num2, 40 * (t + 2)))
            elif "失败" in disneyinfo[t]:
                out.paste(sb2, (1130 + num2, 40 * (t + 2)))
            elif "待解" in disneyinfo[t]:
                out.paste(djs2, (1130 + num2, 40 * (t + 2)))
            else:
                out.paste(na2, (1130 + num2, 40 * (t + 2)))
            d.text((l1, 40 * (t + 2)), text=disneyinfo[t], font=fnt, fill=(0, 0, 0))  # Disney+解锁
            # Youtube
            if "解锁" in youtubeinfo[t]:
                out.paste(cg2, (980 + num2, 40 * (t + 2)))
            elif "失败" in youtubeinfo[t]:
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


def exportImage_old(proxyname: list, info: dict):
    try:

        netflixinfo = info['netflix']
        youtubeinfo = info['youtube']
        disneyinfo = info['disney']
        gpinginfo = info['delay']
        proxytype = info['type']
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
                 "Youtube", "版本:{}     ⏱️总共耗时: {}s".format(__version__, info['wtime']),
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


def color_block(size: tuple, color_value):
    """
    颜色块，颜色数值推荐用十六进制表示如: #ffffff 为白色
    :param size: tuple: (length,width)
    :param color_value: 颜色值
    :return:
    """
    img_block = Image.new('RGB', size, color_value)
    return img_block


class ExportResult:
    """
    生成图片类
    """

    def __init__(self, nodename: list, info: dict):
        self.version = __version__
        self.nodename = nodename
        self.origin_info = info
        self.wtime = info['wtime']
        self.info = info
        del self.info['wtime']
        self.nodetype = info['类型']
        self.nodenum = len(nodename)
        self.front_size = 30
        self.__font = ImageFont.truetype(r"./resources/微软雅黑.ttf", self.front_size)

    def get_height(self):
        return (self.nodenum + 4) * 40

    def get_key_list(self):
        """
        得到测试项名称
        :return: list
        """
        key_list = []
        for i in self.info:
            key_list.append(i)
        return key_list

    def text_width(self, text: str):
        """
        得到字符串在图片中的绘图长度

        :param text: 文本内容
        :return: int
        """
        font = self.__font
        draw = ImageDraw.Draw(Image.new("RGB", (1, 1), (255, 255, 255)))
        textSize = draw.textsize(text, font=font)[0]
        return textSize

    def text_maxwidth(self, strlist: list):
        """
        得到列表中最长字符串的绘图长度

        :param strlist:
        :return: int
        """
        font = self.__font
        draw = ImageDraw.Draw(Image.new("RGB", (1, 1), (255, 255, 255)))
        max_width = 0
        for i in strlist:
            max_width = max(max_width, draw.textsize(str(i), font=font)[0])
        return max_width

    def key_value(self):  # 比较测试项名称和测试项结果的长度
        """
        得到所有测试项列的大小
        :return: list
        """
        key_list = self.get_key_list()  # 得到每个测试项绘图的大小[100,80]
        width_list = []
        max_width = 0
        for i in key_list:
            key_width = self.text_width(i)
            value_width = self.text_maxwidth(self.info[i])
            max_width = max(key_width, value_width)
            max_width = max_width + 45
            width_list.append(max_width)
        return width_list  # 测试项列的大小

    def get_width(self):
        """
        获得整个图片的宽度
        :return:
        """
        img_width = 100  # 序号
        nodename_width = self.text_maxwidth(self.nodename)
        nodename_width = max(nodename_width, 420)
        nodename_width = nodename_width + 60
        infolist_width = self.key_value()
        info_width = 0
        for i in infolist_width:
            info_width = info_width + i
        img_width = img_width + nodename_width + info_width
        return img_width, nodename_width, infolist_width

    def get_mid(self, start, end, str_name):
        """
        居中对齐的起始位置
        :param start:
        :param end:
        :param str_name:
        :return:
        """
        mid_xpath = (end + start) / 2
        strname_width = self.text_width(str_name)
        xpath = mid_xpath - strname_width / 2
        return xpath

    def exportAsPng(self):
        fnt = self.__font
        image_width, nodename_width, info_list_length = self.get_width()
        image_height = self.get_height()
        key_list = self.get_key_list()
        img = Image.new("RGB", (image_width, image_height), (255, 255, 255))
        pilmoji = Pilmoji(img)  # emoji表情修复
        # 绘制色块
        bkg = Image.new('RGB', (image_width, 80), (234, 234, 234))  # 首尾部填充
        img.paste(bkg, (0, 0))
        img.paste(bkg, (0, image_height - 80))
        idraw = ImageDraw.Draw(img)
        # 绘制标题栏与结尾栏
        export_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())  # 输出图片的时间,文件动态命名
        list1 = ["FullTclash - 流媒体测试", "版本:{}     ⏱️总共耗时: {}s".format(__version__, self.wtime),
                 "测试时间: {}  测试结果仅供参考,以实际情况为准".format(export_time)]
        export_time = export_time.replace(':', '-')
        title = list1[0]
        idraw.text((self.get_mid(0, image_width, title), 5), title, font=fnt, fill=(0, 0, 0))  # 标题
        # idraw.text((10, image_height - 75), text=list1[1], font=fnt, fill=(0, 0, 0))  # 版本信息
        pilmoji.text((10, image_height - 75), text=list1[1], font=fnt, fill=(0, 0, 0))
        idraw.text((10, image_height - 35), text=list1[2], font=fnt, fill=(0, 0, 0))  # 测试时间
        '''
        :绘制标签
        '''
        idraw.text((20, 40), '序号', font=fnt, fill=(0, 0, 0))  # 序号
        idraw.text((self.get_mid(100, nodename_width + 100, '节点名称'), 40), '节点名称', font=fnt, fill=(0, 0, 0))  # 节点名称
        start_x = 100 + nodename_width
        m = 0  # 记录测试项数目
        for i in info_list_length:
            x = start_x
            end = start_x + i
            # print(x,end)
            idraw.text((self.get_mid(x, end, key_list[m]), 40), key_list[m], font=fnt, fill=(0, 0, 0))
            # print(self.get_mid(x,end,key_list[m]))
            start_x = end
            m = m + 1
        '''
        :内容填充
        '''
        for t in range(self.nodenum):
            # 序号
            idraw.text((self.get_mid(0, 100, str(t + 1)), 40 * (t + 2)), text=str(t + 1), font=fnt, fill=(0, 0, 0))
            # 节点名称
            # idraw.text((110, 40 * (t + 2)), text=self.nodename[t], font=fnt, fill=(0, 0, 0))
            pilmoji.text((110, 40 * (t + 2)), text=self.nodename[t], font=fnt, fill=(0, 0, 0))
            width = 100 + nodename_width
            i = 0
            # 填充颜色块
            c_block = {'成功': '#bee47e', '失败': '#ee6b73', 'N/A': '#8d8b8e', '待解锁': '#dcc7e1'}
            for t1 in key_list:
                if '解锁' in self.info[t1][t] and '待' not in self.info[t1][t]:
                    block = color_block((info_list_length[i], 40), color_value=c_block['成功'])
                    img.paste(block, (width, 40 * (t + 2)))
                elif '失败' in self.info[t1][t]:
                    block = color_block((info_list_length[i], 40), color_value=c_block['失败'])
                    img.paste(block, (width, 40 * (t + 2)))
                elif '待解' in self.info[t1][t]:
                    block = color_block((info_list_length[i], 40), color_value=c_block['待解锁'])
                    img.paste(block, (width, 40 * (t + 2)))
                elif 'N/A' in self.info[t1][t]:
                    block = color_block((info_list_length[i], 40), color_value=c_block['N/A'])
                    img.paste(block, (width, 40 * (t + 2)))
                else:
                    pass
                width += info_list_length[i]
                i += 1
            width = 100 + nodename_width
            i = 0
            for t2 in key_list:
                idraw.text((self.get_mid(width, width + info_list_length[i], self.info[t2][t]), (t + 2) * 40),
                           self.info[t2][t],
                           font=fnt, fill=(0, 0, 0))
                width += info_list_length[i]
                i += 1
        '''
        :添加横竖线条
        '''
        # 绘制横线
        for t in range(self.nodenum + 3):
            idraw.line([(0, 40 * (t + 1)), (image_width, 40 * (t + 1))], fill="#e1e1e1", width=1)
        # 绘制竖线
        idraw.line([(100, 40), (100, 80)], fill="#e1e1e1", width=2)
        start_x = 100 + nodename_width
        for i in info_list_length:
            x = start_x
            end = start_x + i
            idraw.line([(x, 40), (x, image_height-80)], fill="#e1e1e1", width=2)
            start_x = end
        print(export_time)
        img.save(r"./results/{}.png".format(export_time.replace(':', '-')))
        return export_time
