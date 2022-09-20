from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
import time

"""
这是将测试的结果输出为图片的模块。
设计思路:
1、本项目设计了一个ExportResult类，我们需要两组关键的数据进行初始化：基础数据、各种信息info。
    其中基础数据一般是节点名，info是一个字典，每个字典的键是一个字符串，将是之后的各种测试项标题，如 类型、延迟RTT、Netflix、Youtube等等，
    每个字典键所对应的值即为一个列表。
2、何为基础数据？
    基础数据决定了生成图片的高度（Height），它是列表，列表里面的数据一般是一组节点名，即有多少个节点就对应了info键值中的长度。
"""
__version__ = "3.3.2"  # 版本号


def color_block(size: tuple, color_value):
    """
    颜色块，颜色数值推荐用十六进制表示如: #ffffff 为白色
    :param size: tuple: (length,width)
    :param color_value: 颜色值
    :return: Image
    """
    img_block = Image.new('RGB', size, color_value)
    return img_block


class ExportResult:
    """
    生成图片类
    """

    def __init__(self, info: dict, nodename: list = None):
        self.version = __version__
        self.nodename = nodename
        self.origin_info = info
        self.info = info
        self.nodenum = len(nodename)
        self.front_size = 30
        self.__font = ImageFont.truetype(r"./resources/苹方黑体-准-简.ttf", self.front_size)

    def get_height(self):
        """
        获取图片高度
        :return: int
        """
        return (self.nodenum + 4) * 40

    def get_key_list(self):
        """
        得到测试项名称，即字典里所有键的名称
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
        for i in key_list:
            key_width = self.text_width(i)  # 键的长度
            value_width = self.text_maxwidth(self.info[i])  # 键所对应值的长度
            max_width = max(key_width, value_width)
            max_width = max_width + 40
            width_list.append(max_width)
        return width_list  # 测试项列的大小

    def get_width(self, compare: int = None):
        """
        获得整个图片的宽度,compare参数在这里无用，是继承给子类用的
        :return:
        """
        img_width = 100  # 序号
        nodename_width = self.text_maxwidth(self.nodename)
        nodename_width = max(nodename_width, 420)
        nodename_width = nodename_width + 150
        infolist_width = self.key_value()
        info_width = 0
        for i in infolist_width:
            info_width = info_width + i
        img_width = img_width + nodename_width + info_width
        return img_width, nodename_width, infolist_width

    def get_mid(self, start, end, str_name: str):
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

    def exportUnlock(self):
        wtime = self.info['wtime']
        del self.info['wtime']
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
        list1 = ["FullTclash - 流媒体测试", "版本:{}     ⏱️总共耗时: {}s".format(__version__, wtime),
                 "测试时间: {}  测试结果仅供参考,以实际情况为准".format(export_time)]
        export_time = export_time.replace(':', '-')
        title = list1[0]
        idraw.text((self.get_mid(0, image_width, title), 5), title, font=fnt, fill=(0, 0, 0))  # 标题
        # idraw.text((10, image_height - 75), text=list1[1], font=fnt, fill=(0, 0, 0))  # 版本信息
        pilmoji.text((10, image_height - 75), text=list1[1], font=fnt, fill=(0, 0, 0), emoji_position_offset=(0, 3))
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
            idraw.text((self.get_mid(x, end, key_list[m]), 40), key_list[m], font=fnt, fill=(0, 0, 0))
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
            pilmoji.text((110, 40 * (t + 2)), text=self.nodename[t], font=fnt, fill=(0, 0, 0), emoji_position_offset=(0, 6))
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
            idraw.line([(x, 40), (x, image_height - 80)], fill="#e1e1e1", width=2)
            start_x = end
        print(export_time)
        img.save(r"./results/{}.png".format(export_time.replace(':', '-')))
        return export_time


class ExportTopo(ExportResult):
    """
    生成节点拓扑测试图
    """

    def __init__(self, name: list = None, info: dict = None):
        super().__init__({}, [])
        if name is None:
            self.nodenum = 0
            self.nodename = []
        else:
            self.nodename = name
            self.nodenum = len(name)
        if info is None:
            self.info = {}
        else:
            self.info = info
        self.front_size = 30
        self.__font = ImageFont.truetype(r"./resources/苹方黑体-准-简.ttf", self.front_size)

    def get_width(self, compare: int = None):
        """
        获得整个图片的宽度
        :param: compare 是传入的另一张图片宽度，将与当前图片宽度做比较，目的为了保持两张原本宽度不同的图能宽度一致
        :return:
        """
        img_width = 100  # 序号
        infolist_width = self.key_value()
        info_width = 0
        for i in infolist_width:
            info_width = info_width + i
        img_width = img_width + info_width
        # 如果compare不为空，则将会与当前图片宽度进行比较，取较大值。
        if compare:
            diff = compare - img_width
            if diff > 0:
                img_width = compare
                infolist_width[-1] += diff
        return img_width, infolist_width

    def get_height(self):
        return (self.nodenum + 4) * (self.front_size + 10)

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

    def get_mid(self, start, end, str_name: str):
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

    def get_key_list(self):
        """
        得到测试项名称
        :return: list
        """
        key_list = []
        for i in self.info:
            key_list.append(i)
        return key_list

    def exportTopoInbound(self, nodename: list = None, info2: dict = None, img2_width: int = None):
        # wtime = self.info['wtime']
        wtime = "未知"
        fnt = self.__font
        image_width, info_list_length = self.get_width(compare=img2_width)
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
        list1 = ["FullTclash - 节点拓扑分析", "版本:{}     ⏱️总共耗时: {}".format(__version__, wtime),
                 "测试时间: {}  测试结果仅供参考,以实际情况为准".format(export_time)]
        export_time = export_time.replace(':', '-')
        title = list1[0]
        idraw.text((self.get_mid(0, image_width, title), 1), title, font=fnt, fill=(0, 0, 0))  # 标题
        # idraw.text((10, image_height - 75), text=list1[1], font=fnt, fill=(0, 0, 0))  # 版本信息
        pilmoji.text((10, image_height - 80), text=list1[1], font=fnt, fill=(0, 0, 0), emoji_position_offset=(0, 6))
        idraw.text((10, image_height - 40), text=list1[2], font=fnt, fill=(0, 0, 0))  # 测试时间
        # 绘制标签
        idraw.text((20, 40), '序号', font=fnt, fill=(0, 0, 0))  # 序号
        start_x = 100
        m = 0  # 记录测试项数目
        for i in info_list_length:
            x = start_x
            end = start_x + i
            idraw.text((self.get_mid(x, end, key_list[m]), 40), key_list[m], font=fnt, fill=(0, 0, 0))
            start_x = end
            m = m + 1
        # 内容填充
        for t in range(self.nodenum):
            # 序号
            idraw.text((self.get_mid(0, 100, str(t + 1)), 40 * (t + 2)), text=str(t + 1), font=fnt, fill=(0, 0, 0))
            width = 100
            i = 0
            for t1 in key_list:
                if t1 == "组织":
                    idraw.text((width + 10, (t + 2) * 40),
                               self.info[t1][t],
                               font=fnt, fill=(0, 0, 0))
                elif t1 == "AS编号":
                    idraw.text((self.get_mid(width, width + info_list_length[i], self.info[t1][t]), (t + 2) * 40),
                               self.info[t1][t],
                               font=fnt, fill=(0, 0, 0))
                else:
                    idraw.text((self.get_mid(width, width + info_list_length[i], self.info[t1][t]), (t + 2) * 40),
                               self.info[t1][t],
                               font=fnt, fill=(0, 0, 0))
                width += info_list_length[i]
                i += 1
        # 绘制横线
        for t in range(self.nodenum + 3):
            idraw.line([(0, 40 * (t + 1)), (image_width, 40 * (t + 1))], fill="#e1e1e1", width=1)
        start_x = 100
        for i in info_list_length:
            x = start_x
            end = start_x + i
            idraw.line([(x, 40), (x, image_height - 80)], fill=(255, 255, 255), width=1)
            start_x = end
        if info2 and nodename:
            img2, image_height2, image_width2 = self.exportTopoOutbound(nodename, info2, img2_width=image_width)
            img3 = Image.new("RGB", (max(image_width, image_width2), image_height + image_height2 - 80),
                             (255, 255, 255))
            img3.paste(img, (0, 0))
            img3.paste(img2, (0, image_height - 80))
            print(export_time)
            # img3.show()
            img3.save(r"./results/Topo{}.png".format(export_time.replace(':', '-')))
            return export_time
        else:
            print(export_time)
            img.save(r"./results/Topo{}.png".format(export_time.replace(':', '-')))
            return export_time

    def exportTopoOutbound(self, nodename: list = None, info: dict = None, img2_width: int = None):
        # wtime = self.info['wtime']
        if nodename and info:
            self.__init__(nodename, info)
        wtime = "未知"
        fnt = self.__font
        image_width, info_list_length = self.get_width(compare=img2_width)
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
        list1 = ["出口（提示:出口数量顺数即为每个入口对应节点）", "版本:{}     ⏱️总共耗时: {}".format(__version__, wtime),
                 "测试时间: {}  测试结果仅供参考,以实际情况为准".format(export_time)]
        export_time = export_time.replace(':', '-')
        title = list1[0]
        idraw.text((self.get_mid(0, image_width, title), 1), title, font=fnt, fill=(0, 0, 0))  # 标题
        # idraw.text((10, image_height - 75), text=list1[1], font=fnt, fill=(0, 0, 0))  # 版本信息
        pilmoji.text((10, image_height - 80), text=list1[1], font=fnt, fill=(0, 0, 0), emoji_position_offset=(0, 6))
        idraw.text((10, image_height - 40), text=list1[2], font=fnt, fill=(0, 0, 0))  # 测试时间
        # 绘制标签
        idraw.text((20, 40), '序号', font=fnt, fill=(0, 0, 0))  # 序号
        start_x = 100
        m = 0  # 记录测试项数目
        for i in info_list_length:
            x = start_x
            end = start_x + i
            idraw.text((self.get_mid(x, end, key_list[m]), 40), key_list[m], font=fnt, fill=(0, 0, 0))
            start_x = end
            m = m + 1
        # 内容填充
        for t in range(self.nodenum):
            # 序号
            idraw.text((self.get_mid(0, 100, str(t + 1)), 40 * (t + 2)), text=str(t + 1), font=fnt, fill=(0, 0, 0))
            width = 100
            i = 0
            for t1 in key_list:
                if t1 == "组织":
                    idraw.text((width + 10, (t + 2) * 40),
                               self.info[t1][t],
                               font=fnt, fill=(0, 0, 0))
                elif t1 == "节点名称":
                    pilmoji.text((width + 10, (t + 2) * 40),
                                 self.info[t1][t],
                                 font=fnt, fill=(0, 0, 0), emoji_position_offset=(0, 6))
                else:
                    idraw.text((self.get_mid(width, width + info_list_length[i], self.info[t1][t]), (t + 2) * 40),
                               self.info[t1][t],
                               font=fnt, fill=(0, 0, 0))
                width += info_list_length[i]
                i += 1
        # 绘制横线
        for t in range(self.nodenum + 3):
            idraw.line([(0, 40 * (t + 1)), (image_width, 40 * (t + 1))], fill="#e1e1e1", width=1)
        start_x = 100
        for i in info_list_length:
            x = start_x
            end = start_x + i
            idraw.line([(x, 40), (x, image_height - 80)], fill=(255, 255, 255), width=1)
            start_x = end
        if nodename is None and info is None:
            img.save(r"./results/Topo{}.png".format(export_time.replace(':', '-')))
            print(export_time)
            return export_time
        return img, image_height, image_width
