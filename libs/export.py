import math
import PIL
from loguru import logger
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
from pilmoji.source import Twemoji
import time
from libs.cleaner import ConfigManager
from libs.emoji_custom import TwitterPediaSource

"""
这是将测试的结果输出为图片的模块。
设计思路:
1、本项目设计了一个ExportResult类，我们需要两组关键的数据进行初始化：基础数据、各种信息info。
    其中基础数据一般是节点名，info是一个字典，每个字典的键是一个字符串，将是之后的各种测试项标题，如 类型、延迟RTT、Netflix、Youtube等等，
    每个字典键所对应的值即为一个列表。
2、何为基础数据？
    基础数据决定了生成图片的高度（Height），它是列表，列表里面的数据一般是一组节点名，即有多少个节点就对应了info键值中的长度。
"""
__version__ = "3.5.2"  # 版本号
custom_source = TwitterPediaSource  # 自定义emoji风格 TwitterPediaSource


def color_block(size: tuple, color_value):
    """
    颜色块，颜色数值推荐用十六进制表示如: #ffffff 为白色
    :param size: tuple: (length,width)
    :param color_value: 颜色值
    :return: Image
    """
    img_block = Image.new('RGB', size, color_value)
    return img_block


# TODO(@AirportR): 需要设计个export基类，然后下面三个类继承基类，基类定义一些通用方法
class ExportResult:
    """
    生成图片类
    """

    def __init__(self, info: dict, nodename: list = None):
        self.version = __version__
        self.basedata = info.pop('节点名称', nodename)
        self.info = info
        self.filter = self.info.pop('filter', {})
        self.filter_include = self.filter.get('include', '')
        self.filter_exclude = self.filter.get('exclude', '')
        self.sort = self.info.pop('sort', '订阅原序')
        if self.basedata:
            self.nodenum = len(self.basedata)
        else:
            self.nodenum = 0
        self.front_size = 30
        self.config = ConfigManager()
        self.emoji = self.config.config.get('emoji', True)  # 是否启用emoji，若否，则在输出图片时emoji将无法正常显示
        self.color = self.config.getColor()
        self.image_config = self.config.config.get('image', {})
        self.delay_color = self.color.get('delay', [])
        self.__font = ImageFont.truetype(self.config.getFont(), self.front_size)
        self.title = self.image_config.get('title', 'FullTclash')
        self.watermark = self.image_config.get('watermark', {})
        watermark_default_config = {
            'enable': False,
            'text': '只是一个水印',
            'font_size': 64,
            'color': '#000000',
            'alpha': 16,
            'angle': -16.0,
            'start_y': 0,
            'row_spacing': 0
        }
        for key in watermark_default_config:
            if key not in self.watermark:
                self.watermark[key] = watermark_default_config[key]

    @property
    def interval(self):
        interval_list = []
        for c in self.delay_color:
            interval_list.append(c.get('label', 0))
        a = list(set(interval_list))  # 去重加排序
        a.sort()
        while len(a) < 7:
            a.append(99999)
        if len(a) > 8:
            return a[:8]
        else:
            return a

    @property
    def colorvalue(self):
        color_list = []
        for c in self.delay_color:
            color_list.append(c.get('value', '#f5f3f2'))
        while len(color_list) < 8:
            color_list.append('#f5f3f2')
        if len(color_list) > 8:
            return color_list[:8]
        else:
            return color_list

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
        nodename_width = self.text_maxwidth(self.basedata)
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

    def draw_watermark(self, original_image):
        original_image_size = original_image.size
        watermark_text = self.watermark['text']

        super_sampling_ratio = 3
        font_size = int(self.watermark['font_size'])
        font = ImageFont.truetype(self.config.getFont(), font_size * super_sampling_ratio)

        text_size = font.getsize(watermark_text)
        text_image = Image.new('RGBA', text_size, (255, 255, 255, 0))
        text_draw = ImageDraw.Draw(text_image)

        rgb = tuple(int(self.watermark['color'][i:i + 2], 16) for i in (1, 3, 5))
        text_draw.text((0, 0), watermark_text, (rgb[0], rgb[1], rgb[2], int(self.watermark['alpha'])), font=font)

        rotated_text_image = text_image.rotate(float(self.watermark['angle']), expand=True, fillcolor=(0, 0, 0, 0))
        rotated_text_image_size = [x // super_sampling_ratio for x in rotated_text_image.size]
        if rotated_text_image_size[0] <= 0 or rotated_text_image_size[1] <= 0:
            logger.error(f'无法添加水印，水印大小为:{rotated_text_image_size}')
            return original_image
        rotated_text_image = rotated_text_image.resize(rotated_text_image_size)

        watermarks_image = Image.new('RGBA', original_image_size, (255, 255, 255, 0))

        x = original_image_size[0] // 2 - rotated_text_image_size[0] // 2
        row_spacing = int(self.watermark['row_spacing'])
        if row_spacing < 0:
            row_spacing = 0
        y = int(self.watermark['start_y'])
        while True:
            watermarks_image.paste(rotated_text_image, (x, y))
            y += rotated_text_image_size[1] + row_spacing
            if y >= original_image_size[1]:
                break

        return Image.alpha_composite(original_image, watermarks_image)

    @logger.catch
    def exportUnlock(self):
        wtime = self.info.pop('wtime', "0")
        fnt = self.__font
        image_width, nodename_width, info_list_length = self.get_width()
        image_height = self.get_height()
        key_list = self.get_key_list()
        img = Image.new("RGB", (image_width, image_height), (255, 255, 255))
        pilmoji = Pilmoji(img, source=custom_source)  # emoji表情修复
        # 绘制色块
        bkg = Image.new('RGB', (image_width, 80), (234, 234, 234))  # 首尾部填充
        img.paste(bkg, (0, 0))
        img.paste(bkg, (0, image_height - 80))
        idraw = ImageDraw.Draw(img)
        # 绘制标题栏与结尾栏
        export_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())  # 输出图片的时间,文件动态命名
        list1 = [f"{self.title} - 联通性测试",
                 f"版本:{__version__}   总共耗时: {wtime}s  排序: {self.sort}   " +
                 f"过滤器: {self.filter_include} <-> {self.filter_exclude}",
                 "测试时间: {}  测试结果仅供参考,以实际情况为准".format(export_time)]
        export_time = export_time.replace(':', '-')
        title = list1[0]
        idraw.text((self.get_mid(0, image_width, title), 3), title, font=fnt, fill=(0, 0, 0))  # 标题
        if self.emoji:
            pilmoji.text((10, image_height - 80), text=list1[1], font=fnt, fill=(0, 0, 0), emoji_position_offset=(0, 3))
        else:
            idraw.text((10, image_height - 80), text=list1[1], font=fnt, fill=(0, 0, 0))  # 版本信息
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
        if self.delay_color:
            colorvalue = self.colorvalue
            interval = self.interval
        else:
            # 默认值
            colorvalue = ["#f5f3f2", "#beb1aa", "#f6bec8", "#dc6b82", "#c35c5d", "#8ba3c7", "#c8161d", '#8d8b8e']
            interval = [0, 100, 200, 300, 500, 1000, 2000, 99999]
        # 填充颜色块
        c_block = {'成功': self.color.get('yes', '#bee47e'),
                   '失败': self.color.get('no', '#ee6b73'),
                   'N/A': self.color.get('na', '#8d8b8e'),
                   '待解锁': self.color.get('wait', '#dcc7e1'),
                   'low': self.color.get('iprisk', {}).get('low', '#ffffff'),
                   'medium': self.color.get('iprisk', {}).get('medium', '#ffffff'),
                   'high': self.color.get('iprisk', {}).get('high', '#ffffff'),
                   'veryhigh': self.color.get('iprisk', {}).get('veryhigh', '#ffffff'),
                   '警告': self.color.get('warn', '#fcc43c')
                   }
        for t in range(self.nodenum):
            # 序号
            idraw.text((self.get_mid(0, 100, str(t + 1)), 40 * (t + 2)), text=str(t + 1), font=fnt, fill=(0, 0, 0))
            # 节点名称
            if self.emoji:
                try:
                    # 自定义emoji源可能出错，所以捕捉了异常
                    pilmoji.text((110, 40 * (t + 2)), text=self.basedata[t], font=fnt, fill=(0, 0, 0),
                                 emoji_position_offset=(0, 6))
                except PIL.UnidentifiedImageError:
                    logger.warning("无效符号:" + self.basedata[t])
                    pilmoji2 = Pilmoji(img, source=Twemoji)
                    pilmoji2.text((110, 40 * (t + 2)), text=self.basedata[t], font=fnt, fill=(0, 0, 0),
                                  emoji_position_offset=(0, 6))
            else:
                idraw.text((110, 40 * (t + 2)), text=self.basedata[t], font=fnt, fill=(0, 0, 0))

            width = 100 + nodename_width
            i = 0
            for t1 in key_list:
                if "延迟RTT" == t1 or "HTTP延迟" == t1:
                    rtt = float(self.info[t1][t][:-2])
                    if interval[0] < rtt < interval[1]:
                        block = color_block((info_list_length[i], 40), color_value=colorvalue[0])
                        img.paste(block, (width, 40 * (t + 2)))
                    elif interval[1] <= rtt < interval[2]:
                        block = color_block((info_list_length[i], 40), color_value=colorvalue[1])
                        img.paste(block, (width, 40 * (t + 2)))
                    elif interval[2] <= rtt < interval[3]:
                        block = color_block((info_list_length[i], 40), color_value=colorvalue[2])
                        img.paste(block, (width, 40 * (t + 2)))
                    elif interval[3] <= rtt < interval[4]:
                        block = color_block((info_list_length[i], 40), color_value=colorvalue[3])
                        img.paste(block, (width, 40 * (t + 2)))
                    elif interval[4] <= rtt < interval[5]:
                        block = color_block((info_list_length[i], 40), color_value=colorvalue[4])
                        img.paste(block, (width, 40 * (t + 2)))
                    elif interval[5] <= rtt < interval[6]:
                        block = color_block((info_list_length[i], 40), color_value=colorvalue[5])
                        img.paste(block, (width, 40 * (t + 2)))
                    elif interval[6] <= rtt:
                        block = color_block((info_list_length[i], 40), color_value=colorvalue[6])
                        img.paste(block, (width, 40 * (t + 2)))
                    elif rtt == 0:
                        block = color_block((info_list_length[i], 40), color_value=colorvalue[7])
                        img.paste(block, (width, 40 * (t + 2)))
                elif ('解锁' in self.info[t1][t] or '允许' in self.info[t1][t]) and '待' not in self.info[t1][t]:
                    block = color_block((info_list_length[i], 40), color_value=c_block['成功'])
                    img.paste(block, (width, 40 * (t + 2)))
                elif '失败' in self.info[t1][t] or '禁止' in self.info[t1][t]:
                    block = color_block((info_list_length[i], 40), color_value=c_block['失败'])
                    img.paste(block, (width, 40 * (t + 2)))
                elif '待解' in self.info[t1][t]:
                    block = color_block((info_list_length[i], 40), color_value=c_block['待解锁'])
                    img.paste(block, (width, 40 * (t + 2)))
                elif 'N/A' in self.info[t1][t]:
                    block = color_block((info_list_length[i], 40), color_value=c_block['N/A'])
                    img.paste(block, (width, 40 * (t + 2)))
                elif 'Low' in self.info[t1][t]:
                    block = color_block((info_list_length[i], 40), color_value=c_block['low'])
                    img.paste(block, (width, 40 * (t + 2)))
                elif 'Medium' in self.info[t1][t]:
                    block = color_block((info_list_length[i], 40), color_value=c_block['medium'])
                    img.paste(block, (width, 40 * (t + 2)))
                elif 'High' in self.info[t1][t] and 'Very' not in self.info[t1][t]:
                    block = color_block((info_list_length[i], 40), color_value=c_block['high'])
                    img.paste(block, (width, 40 * (t + 2)))
                elif 'Very' in self.info[t1][t]:
                    block = color_block((info_list_length[i], 40), color_value=c_block['veryhigh'])
                    img.paste(block, (width, 40 * (t + 2)))
                elif '超时' in self.info[t1][t] or '连接错误' in self.info[t1][t]:
                    block = color_block((info_list_length[i], 40), color_value=c_block['警告'])
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
            idraw.line([(0, 40 * (t + 1)), (image_width, 40 * (t + 1))], fill="#e1e1e1", width=2)
        # 绘制竖线
        idraw.line([(100, 40), (100, 80)], fill="#e1e1e1", width=2)
        start_x = 100 + nodename_width
        for i in info_list_length:
            x = start_x
            end = start_x + i
            idraw.line([(x, 40), (x, image_height - 80)], fill="#e1e1e1", width=2)
            start_x = end
        print(export_time)
        if self.watermark['enable']:
            img = self.draw_watermark(img.convert("RGBA"))
        img.save(r"./results/{}.png".format(export_time.replace(':', '-')))
        return export_time


class ExportTopo(ExportResult):
    """
    生成节点拓扑测试图
    """

    def __init__(self, name: list = None, info: dict = None):
        super().__init__({})
        if info is None:
            self.info = {}
        else:
            self.info = info
        if name is None:
            self.basedata = self.info.get('节点名称', []) if '节点名称' in self.info else self.info.get('地区', [])
        else:
            self.basedata = self.info.get('节点名称', name) if '节点名称' in self.info else self.info.get('地区', [])
        self.emoji = self.config.config.get('emoji', True)  # 是否启用emoji，若否，则在输出图片时emoji将无法正常显示
        self.wtime = self.info.pop('wtime', "未知")
        self.nodenum = len(self.basedata)
        self.front_size = 30
        self.config = ConfigManager()
        self.__font = ImageFont.truetype(self.config.getFont(), self.front_size)
        # self.image_config = self.config.config.get('image', {})
        # self.title = self.image_config.get('title', 'FullTclash')

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

    @logger.catch
    def exportTopoInbound(self, nodename: list = None, info2: dict = None, img2_width: int = None):
        fnt = self.__font
        image_width, info_list_length = self.get_width(compare=img2_width)
        image_height = self.get_height()
        key_list = self.get_key_list()
        img = Image.new("RGB", (image_width, image_height), (255, 255, 255))
        pilmoji = Pilmoji(img, source=custom_source)  # emoji表情修复
        # 绘制色块
        bkg = Image.new('RGB', (image_width, 80), (234, 234, 234))  # 首尾部填充
        img.paste(bkg, (0, 0))
        img.paste(bkg, (0, image_height - 80))
        idraw = ImageDraw.Draw(img)
        # 绘制标题栏与结尾栏
        export_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())  # 输出图片的时间,文件动态命名
        list1 = [f"{self.title} - 节点拓扑分析", "版本:{}   总共耗时: {}s".format(__version__, self.wtime),
                 "测试时间: {}  测试结果仅供参考".format(export_time)]
        export_time = export_time.replace(':', '-')
        title = list1[0]
        idraw.text((self.get_mid(0, image_width, title), 1), title, font=fnt, fill=(0, 0, 0))  # 标题

        if self.emoji:
            pilmoji.text((10, image_height - 80), text=list1[1], font=fnt, fill=(0, 0, 0), emoji_position_offset=(0, 6))
        else:
            idraw.text((10, image_height - 80), text=list1[1], font=fnt, fill=(0, 0, 0))  # 版本信息
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
        # cu = self.info.pop('簇', [1 for _ in range(self.nodenum)])
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
                    idraw.text((self.get_mid(width, width + info_list_length[i], str(self.info[t1][t])), (t + 2) * 40),
                               str(self.info[t1][t]),
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

            if self.watermark['enable']:
                img3 = self.draw_watermark(img3.convert("RGBA"))
            print(export_time)
            # img3.show()
            img3.save(r"./results/Topo{}.png".format(export_time.replace(':', '-')))
            return export_time
        else:
            if self.watermark['enable']:
                img = self.draw_watermark(img.convert("RGBA"))
            print(export_time)
            img.save(r"./results/Topo{}.png".format(export_time.replace(':', '-')))
            return export_time

    @logger.catch
    def exportTopoOutbound(self, nodename: list = None, info: dict = None, img2_width: int = None):
        if nodename or info:
            self.__init__(nodename, info)
        fnt = self.__font
        image_width, info_list_length = self.get_width(compare=img2_width)
        image_height = self.get_height()
        key_list = self.get_key_list()
        img = Image.new("RGB", (image_width, image_height), (255, 255, 255))
        pilmoji = Pilmoji(img, source=custom_source)  # emoji表情修复
        # 绘制色块
        bkg = Image.new('RGB', (image_width, 80), (234, 234, 234))  # 首尾部填充
        img.paste(bkg, (0, 0))
        img.paste(bkg, (0, image_height - 80))
        idraw = ImageDraw.Draw(img)
        # 绘制标题栏与结尾栏
        export_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())  # 输出图片的时间,文件动态命名
        list1 = ["出口分析", "版本:{}  总共耗时: {}s".format(__version__, self.wtime),
                 "测试时间: {}  测试结果仅供参考,以实际情况为准。簇代表节点复用。".format(export_time)]
        export_time = export_time.replace(':', '-')
        title = list1[0]
        idraw.text((self.get_mid(0, image_width, title), 1), title, font=fnt, fill=(0, 0, 0))  # 标题
        if self.emoji:
            pilmoji.text((10, image_height - 80), text=list1[1], font=fnt, fill=(0, 0, 0), emoji_position_offset=(0, 6))
        else:
            idraw.text((10, image_height - 80), text=list1[1], font=fnt, fill=(0, 0, 0))  # 版本信息
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
        # 绘制横线
        # for t in range(self.nodenum + 3):
        #     idraw.line([(0, 40 * (t + 1)), (image_width, 40 * (t + 1))], fill="#e1e1e1", width=2)
        # 内容填充
        cu = self.info.get('簇', [1 for _ in range(self.nodenum)])
        cu_offset = 0
        cu_offset2 = 0
        for t in range(self.nodenum):
            # 序号
            idraw.text((self.get_mid(0, 100, str(t + 1)), 40 * (t + 2)), text=str(t + 1), font=fnt, fill=(0, 0, 0))
            idraw.line([(0, 40 * (t + 3)), (100, 40 * (t + 3))], fill="#e1e1e1", width=2)
            width = 100
            i = 0
            if t < len(cu):
                if cu[t] > 1:
                    cu_offset2 += cu[t] - 1
            for t1 in key_list:
                if t1 == "地区" or t1 == "AS编号":
                    if t < len(cu):
                        temp = cu[t]
                        y = ((t + 2) * 40 + (t + 2) * 40 + (40 * (temp - 1))) / 2 + cu_offset * 40
                        idraw.text((self.get_mid(width, width + info_list_length[i], str(self.info[t1][t])), y),
                                   str(self.info[t1][cu_offset + t]),
                                   font=fnt, fill=(0, 0, 0))
                        idraw.line([(width, (t + 3 + cu_offset2) * 40),
                                    (width + info_list_length[i], (t + 3 + cu_offset2) * 40)],
                                   fill="#e1e1e1", width=2)
                elif t1 == "组织":
                    if t < len(cu):
                        temp = cu[t]
                        y = ((t + 2) * 40 + (t + 2) * 40 + (40 * (temp - 1))) / 2 + cu_offset * 40
                        idraw.text((width + 10, y),
                                   str(self.info[t1][cu_offset + t]),
                                   font=fnt, fill=(0, 0, 0))
                        idraw.line([(width, (t + 3 + cu_offset2) * 40),
                                    (width + info_list_length[i], (t + 3 + cu_offset2) * 40)],
                                   fill="#e1e1e1", width=2)
                elif t1 == "簇":
                    if t < len(cu):
                        temp = self.info[t1][t]
                        y = ((t + 2) * 40 + (t + 2) * 40 + (40 * (temp - 1))) / 2 + cu_offset * 40
                        idraw.text((self.get_mid(width, width + info_list_length[i], str(self.info[t1][t])), y),
                                   str(self.info[t1][t]),
                                   font=fnt, fill=(0, 0, 0))
                        if cu[t] > 1:
                            cu_offset += cu[t] - 1
                        idraw.line([(width, (t + 3 + cu_offset2) * 40),
                                    (width + info_list_length[i], (t + 3 + cu_offset2) * 40)],
                                   fill="#e1e1e1", width=2)
                    else:
                        pass
                elif t1 == "节点名称":
                    try:
                        if self.emoji:
                            pilmoji.text((width + 10, (t + 2) * 40),
                                         self.info[t1][t],
                                         font=fnt, fill=(0, 0, 0), emoji_position_offset=(0, 6))
                        else:
                            idraw.text((width + 10, (t + 2) * 40), self.info[t1][t], font=fnt, fill=(0, 0, 0))
                    except PIL.UnidentifiedImageError:
                        logger.warning("无效符号:" + self.basedata[t])
                        pilmoji2 = Pilmoji(img, source=Twemoji)
                        pilmoji2.text((width + 10, (t + 2) * 40),
                                      self.info[t1][t],
                                      font=fnt, fill=(0, 0, 0), emoji_position_offset=(0, 6))
                    except Exception as e:
                        logger.error(str(e))
                        idraw.text((width + 10, (t + 2) * 40), self.info[t1][t], font=fnt, fill=(0, 0, 0))
                    idraw.line(
                        [(width, (t + 3) * 40), (width + info_list_length[i], (t + 3) * 40)],
                        fill="#e1e1e1", width=2)
                elif t1 == "入口":
                    text = str(self.info[t1][t])
                    pre_text = str(self.info[t1][t - 1]) if t > 0 else str(self.info[t1][0])
                    if t == 0:
                        idraw.text(
                            (self.get_mid(width, width + info_list_length[i], str(self.info[t1][t])), (t + 2) * 40),
                            str(self.info[t1][t]),
                            font=fnt, fill=(0, 0, 0))
                    elif text != pre_text:
                        idraw.text(
                            (self.get_mid(width, width + info_list_length[i], text), (t + 2) * 40),
                            text,
                            font=fnt, fill=(0, 0, 0))
                    else:
                        pass
                else:
                    idraw.text((self.get_mid(width, width + info_list_length[i], str(self.info[t1][t])), (t + 2) * 40),
                               str(self.info[t1][t]),
                               font=fnt, fill=(0, 0, 0))
                width += info_list_length[i]
                i += 1
        idraw.line([(0, 40), (image_width, 40)], fill="#e1e1e1", width=2)
        idraw.line([(0, image_height - 40), (image_width, image_height - 40)], fill="#e1e1e1", width=2)
        start_x = 100
        for i in info_list_length:
            x = start_x
            end = start_x + i
            idraw.line([(x, 40), (x, image_height - 80)], fill=(255, 255, 255), width=1)
            start_x = end
        if nodename is None and info is None:
            if self.watermark['enable']:
                img = self.draw_watermark(img.convert("RGBA"))
            img.save(r"./results/Topo{}.png".format(export_time.replace(':', '-')))
            print(export_time)
            return export_time
        return img, image_height, image_width


class ExportSpeed(ExportResult):
    def __init__(self, name: list = None, info: dict = None):
        """
        速度测试图输出
        :param name:
        :param info:
        """
        super().__init__({}, [])
        self.config = ConfigManager()
        self.color = self.config.getColor().get('speed', [])
        self.emoji = self.config.config.get('emoji', True)  # 是否启用emoji，若否，则在输出图片时emoji将无法正常显示
        if info is None:
            info = {}
        self.wtime = info.pop('wtime', "-1")
        self.filter = info.pop('filter', {})
        self.filter_include = self.filter.get('include', '')
        self.filter_exclude = self.filter.get('exclude', '')
        self.thread = str(info.pop('线程', ''))
        self.traffic = "%.1f" % info.pop('消耗流量', 0)
        self.info = info
        self.basedata = info.pop('节点名称', name)
        if self.basedata:
            self.nodenum = len(self.basedata)
        else:
            self.nodenum = 0
        self.front_size = 30
        self.config = ConfigManager()
        self.__font = ImageFont.truetype(self.config.getFont(), self.front_size)
        self.speedblock_width = 20

    def key_value(self):
        """
        得到所有测试项列的大小
        :return: list
        """
        key_list = self.get_key_list()  # 得到每个测试项绘图的大小[100,80]
        width_list = []
        for i in key_list:
            key_width = self.text_width(i)  # 键的长度
            max_width = 0
            if self.info[i]:
                if i == '速度变化':
                    key_width += 40
                    speedblock_count = max([len(lst) for lst in self.info[i]])
                    if speedblock_count > 0:
                        speedblock_total_width = speedblock_count * self.speedblock_width
                        if speedblock_total_width >= key_width:
                            max_width = speedblock_total_width
                        else:
                            self.speedblock_width = math.ceil(key_width / speedblock_count)
                            max_width = speedblock_count * self.speedblock_width
                    else:
                        max_width = key_width
                else:
                    value_width = self.text_maxwidth(self.info[i])  # 键所对应值的长度
                    max_width = max(key_width, value_width)
                    max_width += 40

            width_list.append(max_width)
        return width_list  # 测试项列的大小

    @property
    def interval(self):
        interval_list = []
        for c in self.color:
            interval_list.append(c.get('label', 0))
        a = list(set(interval_list))  # 去重加排序
        a.sort()
        '''
        while len(a) < 7:
            a.append(99999)
        if len(a) > 7:
            return a[:7]
        else:
            return a
        '''
        return a

    @property
    def colorvalue(self):
        color_list = []
        for c in self.color:
            color_list.append(c.get('value', '#f5f3f2'))
        '''
        while len(color_list) < 7:
            color_list.append('#f5f3f2')
        if len(color_list) > 7:
            return color_list[:7]
        else:
            return color_list
        '''
        return color_list

    @logger.catch
    def exportImage(self):
        fnt = self.__font
        image_width, nodename_width, info_list_length = self.get_width()
        image_height = self.get_height()
        key_list = self.get_key_list()
        img = Image.new("RGB", (image_width, image_height), (255, 255, 255))
        pilmoji = Pilmoji(img, source=custom_source)  # emoji表情修复
        # 绘制色块
        bkg = Image.new('RGB', (image_width, 80), (234, 234, 234))  # 首尾部填充
        img.paste(bkg, (0, 0))
        img.paste(bkg, (0, image_height - 80))
        idraw = ImageDraw.Draw(img)
        # 绘制标题栏与结尾栏
        export_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())  # 输出图片的时间,文件动态命名
        list1 = [f"{self.title} - 速度测试",
                 f"版本:{__version__}    总共耗时: {self.wtime}s   消耗流量: {self.traffic}MB   线程: {self.thread}" +
                 f"过滤器: {self.filter_include} <-> {self.filter_exclude}",
                 "测试时间: {}  测试结果仅供参考,以实际情况为准".format(export_time)]
        export_time = export_time.replace(':', '-')
        title = list1[0]
        idraw.text((self.get_mid(0, image_width, title), 5), title, font=fnt, fill=(0, 0, 0))  # 标题
        if self.emoji:
            pilmoji.text((10, image_height - 75), text=list1[1], font=fnt, fill=(0, 0, 0), emoji_position_offset=(0, 3))
        else:
            idraw.text((10, image_height - 75), text=list1[1], font=fnt, fill=(0, 0, 0))  # 版本信息
        idraw.text((10, image_height - 35), text=list1[2], font=fnt, fill=(0, 0, 0))  # 测试时间

        # 绘制标签
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
        if self.color:
            colorvalue = self.colorvalue
            interval = self.interval
        else:
            # 默认值
            colorvalue = ["#f5f3f2", "#beb1aa", "#f6bec8", "#dc6b82", "#c35c5d", "#8ba3c7", "#c8161d"]
            interval = [0, 1, 5, 10, 20, 60, 100]
        for t in range(self.nodenum):
            # 序号
            idraw.text((self.get_mid(0, 100, str(t + 1)), 40 * (t + 2)), text=str(t + 1), font=fnt, fill=(0, 0, 0))
            # 节点名称
            if self.emoji:
                try:
                    # 自定义emoji源可能出错，所以捕捉了异常
                    pilmoji.text((110, 40 * (t + 2)), text=self.basedata[t], font=fnt, fill=(0, 0, 0),
                                 emoji_position_offset=(0, 6))
                except PIL.UnidentifiedImageError:
                    logger.warning("无效符号:" + self.basedata[t])
                    pilmoji2 = Pilmoji(img, source=Twemoji)
                    pilmoji2.text((110, 40 * (t + 2)), text=self.basedata[t], font=fnt, fill=(0, 0, 0),
                                  emoji_position_offset=(0, 6))
            else:
                idraw.text((110, 40 * (t + 2)), text=self.basedata[t], font=fnt, fill=(0, 0, 0))

            def get_color(speedvalue, default_color='#C0C0C0'):
                for i in reversed(range(len(colorvalue))):
                    if speedvalue >= interval[i]:
                        return colorvalue[i]
                return default_color

            width = 100 + nodename_width + 2
            i = 0
            speedblock_height = 40
            # 填充颜色块
            for t1 in key_list:
                if t1 == "平均速度" or t1 == "最大速度":
                    speedvalue = float(self.info[t1][t][:-2])
                    block = color_block((info_list_length[i], speedblock_height), color_value=get_color(speedvalue))
                    img.paste(block, (width, speedblock_height * (t + 2)))
                elif t1 == "速度变化":
                    speedblock_x = width
                    for speedvalue in self.info[t1][t]:
                        max_speed = float(self.info["最大速度"][t][:-2])
                        if (max_speed > 0.0):
                            speedblock_ratio_height = int(speedblock_height * speedvalue / max_speed)
                            if (speedblock_ratio_height > speedblock_height):
                                speedblock_ratio_height = speedblock_height
                            speedblock_y = speedblock_height * (t + 2) + (speedblock_height - speedblock_ratio_height)

                            block = color_block((self.speedblock_width, speedblock_ratio_height),
                                                color_value=get_color(speedvalue))
                            img.paste(block, (speedblock_x, speedblock_y))
                        speedblock_x += self.speedblock_width
                width += info_list_length[i]
                i += 1

            # 填充字符
            width = 100 + nodename_width
            i = 0
            for t2 in key_list:
                if type(self.info[t2][t]) == str:
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
        if self.watermark['enable']:
            img = self.draw_watermark(img.convert("RGBA"))
        img.save(r"./results/{}.png".format(export_time.replace(':', '-')))
        return export_time
