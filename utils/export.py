import bisect
import math
import time
from typing import Union, Tuple

import PIL
import datetime

from loguru import logger
from PIL import Image, ImageDraw, ImageFont, ImageColor
from pilmoji import Pilmoji
from pilmoji.source import Twemoji

from utils.cleaner import ConfigManager
import utils.emoji_custom as emoji_source

__version__ = '3.6.0'

# 这是将测试的结果输出为图片的模块。
# 设计思路:
# 1、本项目设计了一个ExportResult类，我们需要两组关键的数据进行初始化：基础数据、各种信息info。
#     其中基础数据一般是节点名，info是部字典，每部字典的键是一个字符串，将是之后的各种测试项标题，如 类型、延迟RTT、Netflix、Youtube等等，
#     每个字典键所对应的值即为一个列表。
# 2、何为基础数据？
#     基础数据决定了生成图片的高度（Height），它是列表，列表里面的数据一般是一组节点名，有多少个节点就对应了info键值中的长度。

_clock_emoji_list = ["🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚"]


def get_clock_emoji() -> str:
    current_hour = time.localtime().tm_hour % 12
    emoji_time = _clock_emoji_list[current_hour]
    return emoji_time


def getrgb(hexcolor: str):
    """
    转换16进制格式的颜色值到RGB格式
    """
    if hexcolor.startswith('#'):
        return tuple(int(hexcolor.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
    else:
        raise ValueError("颜色值必须为十六进制")


def color_block(size: Tuple[int, int], color_value: str, alpha: int):
    """
    颜色块，颜色数值推荐用十六进制表示如: #ffffff 为白色
    :param size: tuple: (length,width)
    :param color_value: str: 颜色值
    :param alpha: int: 透明度, 默认为 255 (不透明)
    :return: Image
    """
    rgba = getrgb(color_value) + (alpha,)
    return Image.new('RGBA', size, rgba)


def c_block_grad(size: Tuple[int, int], color_value: str, end_color: str, alpha: int = 255):
    """
    生成渐变色块
    :param size: tuple: (length, width) 图像尺寸
    :param color_value: str: 起始颜色值，十六进制表示
    :param end_color: str: 结束颜色值，十六进制表示
    :param alpha: int: 透明度，默认为 255 (不透明)
    :return: Image
    """
    image = Image.new('RGBA', size)
    draw = ImageDraw.Draw(image)
    start_rgb = getrgb(color_value)
    end_rgb = getrgb(end_color)

    for y in range(size[1]):
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * (y / size[1]))
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * (y / size[1]))
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * (y / size[1]))
        rgba = (r, g, b, alpha)
        draw.line([(0, y), (size[0], y)], fill=rgba)

    return image


class BaseExport:
    def __init__(self, primarykey: Union[list, tuple], allinfo: dict):
        """
        所有绘图类的基类，primarykey为主键，计算主键的长度，主键决定整张图片的高度
        """
        self.basedata = primarykey
        self.allinfo = allinfo
        self.info = self.getPrintinfo()

    def getPrintinfo(self):
        """
        为了统一长度，self.info 一定和主键长度对齐
        """
        new_info = {}
        for k, v in self.allinfo.items():
            if isinstance(v, list) and len(v) == len(self.basedata):
                new_info[k] = v
        return new_info


class ExportCommon(BaseExport):
    def __init__(self, primarykey: Union[list, tuple], allinfo: dict):
        """
        一种通用的绘图数据表格类，连通性测试一般是用这个。
        Args:
            primarykey: 将一个列表的数据作为基底，来决定整张图片的高度
            allinfo: 所有的数据传入，它应该是一个字典
        """
        super().__init__(primarykey, allinfo)
        self.nodenum = len(self.basedata) if self.basedata else 0
        self.filter = self.allinfo.pop('filter', {})
        self.config = ConfigManager()
        self.front_size = 38
        self.linespace = 65
        self._font = ImageFont.truetype(self.config.getFont(), self.front_size)
        self.end_colors = self.config.config.get('end_colors_switch', False)
        self.image_config = self.config.config.get('image', {})
        self.color = self.config.getColor()

        self.emoji = self.config.config.get('emoji', {}).get('enable', True)
        emoji_source_name = self.config.config.get('emoji', {}).get('emoji-source', "TwemojiLocalSource")
        self.emoji_source = getattr(emoji_source, emoji_source_name) if emoji_source_name in emoji_source.__all__ \
            else emoji_source.TwemojiLocalSource

        # 以下这个变量保存着大多数绘图相关的值，比如字体大小、绘图标题这些，这样看是不是更整齐美观了呢
        self.image = {
            'wtime': self.allinfo.pop('wtime', "未知"),
            'filter_include': self.filter.pop('include', ''),
            'filter_exclude': self.filter.pop('exclude', ''),
            'sort': self.allinfo.pop('sort', '订阅原序'),
            'front_size': self.front_size,  # 字体大小
            'linespace': self.linespace,  # 行距,约定60行间距为标准行间距
            'title': self.image_config.get('title', 'FullTclash'),
            'background': self.image_config.get('background', {}),
            'delay_color': self.color.get('delay', []),
            'watermark': self.watermark_config(),
            'height': self.get_height(),
            'widths': self.get_width(),  # 注意，这个键的值是个长度为3的元组，并非单个值。
            'ctofs': int(self.linespace / 2 - self.front_size / 2),  # 行间距改变时的补偿偏移量,Compensation offsets。
        }
        self.init_color_config()

    def watermark_config(self) -> dict:
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
        new_watermark = self.image_config.get('watermark', {})
        for key in watermark_default_config:
            if key in new_watermark:
                watermark_default_config[key] = new_watermark[key]
        return watermark_default_config

    def init_color_config(self):
        """
        对配置中获取的颜色进行预处理，使之变得合理。
        """
        interval_list = []
        alphas_list = []
        color_list = []
        end_color_list = []

        # 这里判断是否自己配置了颜色
        if not self.image['delay_color']:
            colorvalue = ["#f5f3f2", "#c3fae8", "#66d9e8", "#74c0fc", "#748ffc", "#845ef7", "#be4bdb", '#8d8b8e']
            end_color = ["#f5f3f2", "#c3fae8", "#66d9e8", "#74c0fc", "#748ffc", "#845ef7", "#be4bdb", '#8d8b8e']
            interval = [0, 100, 200, 300, 500, 1000, 2000, 99999]
            alphas = [255, 255, 255, 255, 255, 255, 255, 255]
            self.image['interval'] = interval
            self.image['alphas'] = alphas
            self.image['colorvalue'] = colorvalue
            self.image['end_color'] = end_color
            return

        delay_color = sorted(self.image['delay_color'], key=lambda x: x["label"])
        for c in delay_color:
            interval_list.append(c.get('label', 0))
            alphas_list.append(c.get('alpha', 255))
            color_list.append(c.get('value', '#f5f3f2'))
            if "end_color" in c:
                end_color_list.append(c.get('end_color', '#f5f3f2'))
            else:
                end_color_list.append(c.get('value', '#f5f3f2'))

        # print("排序后的结果为：", interval_list)

        self.image['interval'] = interval_list
        self.image['alphas'] = alphas_list
        self.image['colorvalue'] = color_list
        self.image['end_color'] = end_color_list

    @property
    def c_block(self):
        return {'成功': self.color.get('yes', '#BEE587'),
                '失败': self.color.get('no', '#ef6b73'),
                'N/A': self.color.get('na', '#8d8b8e'),
                '待解锁': self.color.get('wait', '#dcc7e1'),
                'low': self.color.get('iprisk', {}).get('low', '#ffffff'),
                'medium': self.color.get('iprisk', {}).get('medium', '#ffffff'),
                'high': self.color.get('iprisk', {}).get('high', '#ffffff'),
                'veryhigh': self.color.get('iprisk', {}).get('veryhigh', '#ffffff'),
                '警告': self.color.get('warn', '#fcc43c'),
                '未知': self.color.get('weizhi', '#5ccfe6'),
                '自制': self.color.get('zhizhi', '#ffffff'),
                '海外': self.color.get('haiwai', '#FFE66B'),
                }

    @property
    def c_alpha(self):
        return {'成功': self.color.get('yesalpha', 255),
                '失败': self.color.get('noalpha', 255),
                'N/A': self.color.get('naalpha', 255),
                '待解锁': self.color.get('waitalpha', 255),
                'low': self.color.get('iprisk', {}).get('lowalpha', 255),
                'medium': self.color.get('iprisk', {}).get('mediumalpha', 255),
                'high': self.color.get('iprisk', {}).get('highalpha', 255),
                'veryhigh': self.color.get('iprisk', {}).get('veryhighalpha', 255),
                '警告': self.color.get('warnalpha', 255),
                '未知': self.color.get('weizhialpha', 255),
                '自制': self.color.get('zhizhialpha', 255),
                '海外': self.color.get('haiwaialpha', 255),
                }

    @property
    def c_end_color(self):
        if self.end_colors:
            c_end_color = {'成功': self.color.get('yesend', '#BEE587'),
                           '失败': self.color.get('noend', '#ef6b73'),
                           'N/A': self.color.get('naend', '#8d8b8e'),
                           '待解锁': self.color.get('waitend', '#dcc7e1'),
                           'low': self.color.get('iprisk', {}).get('lowend', '#ffffff'),
                           'medium': self.color.get('iprisk', {}).get('mediumend', '#ffffff'),
                           'high': self.color.get('iprisk', {}).get('highend', '#ffffff'),
                           'veryhigh': self.color.get('iprisk', {}).get('veryhighend', '#ffffff'),
                           '警告': self.color.get('warnend', '#fcc43c'),
                           '未知': self.color.get('weizhiend', '#5ccfe6'),
                           '自制': self.color.get('zhizhiend', '#ffffff'),
                           '海外': self.color.get('haiwaiend', '#FFE66B'),
                           }
        else:
            c_end_color = {'成功': self.color.get('yes', '#BEE587'),
                           '失败': self.color.get('no', '#ef6b73'),
                           'N/A': self.color.get('na', '#8d8b8e'),
                           '待解锁': self.color.get('wait', '#dcc7e1'),
                           'low': self.color.get('iprisk', {}).get('low', '#ffffff'),
                           'medium': self.color.get('iprisk', {}).get('medium', '#ffffff'),
                           'high': self.color.get('iprisk', {}).get('high', '#ffffff'),
                           'veryhigh': self.color.get('iprisk', {}).get('veryhigh', '#ffffff'),
                           '警告': self.color.get('warn', '#fcc43c'),
                           '未知': self.color.get('weizhi', '#5ccfe6'),
                           '自制': self.color.get('zhizhi', '#ffffff'),
                           '海外': self.color.get('haiwai', '#FFE66B'),
                           }
        return c_end_color

    @property
    def interval(self) -> list:
        return self.image.get('interval', [])

    @property
    def alphas(self) -> list:
        return self.image.get('alphas', [])

    @property
    def colorvalue(self) -> list:
        return self.image.get('colorvalue', [])

    @property
    def end_color(self) -> list:
        return self.image.get('end_color', [])

    def text_width(self, text: str) -> int:
        """
        得到字符串在图片中的绘图长度
        :param text: 文本内容
        :return: int
        """
        draw = ImageDraw.Draw(Image.new("RGBA", (1, 1), (255, 255, 255, 255)))
        return int(draw.textlength(text, font=self._font))

    def text_maxwidth(self, strlist: list) -> int:
        """
        得到列表中最长字符串的绘图长度
        :param strlist:
        :return: int
        """
        max_width = max(self.text_width(str(i)) for i in strlist) if strlist else 0
        return max_width

    def key_width_list(self) -> list:
        """
        得到所有测试项列的大小
        :return: list
        """
        key_list = self.get_key_list()  # 得到每个测试项便签绘图的大小[100,80]
        width_list = []
        for i in key_list:
            key_width = self.text_width(i)  # 键的长度
            value_width = self.text_maxwidth(self.info[i])  # 键所对应值的长度
            max_width = max(key_width, value_width) + 65  # 65为缓冲值，为了不让字距离边界那么近
            width_list.append(max_width)
        return width_list  # 测试项列的大小

    def get_key_list(self) -> list:
        """
        得到测试项名称，即字典里所有键的名称
        :return: list
        """
        return list(self.info.keys())

    def get_height(self) -> int:
        """
        获取图片高度
        :return: int
        """
        return (self.nodenum + 4) * self.linespace

    def get_width(self, compare: int = None):
        """
        获得整个图片的宽度,compare参数在这里无用，是继承给子类用的
        :return:
        """
        if compare:
            print(compare)
        img_width = 100  # 序号
        nodename_width = self.text_maxwidth(self.basedata)
        nodename_width = max(nodename_width, 500)
        nodename_width = nodename_width + 150

        infolist_width = self.key_width_list()
        info_width = sum(infolist_width)

        img_width = img_width + nodename_width + info_width
        return img_width, nodename_width, infolist_width

    def get_mid(self, start_x: Union[int, float], end_x: Union[int, float], str_name: str) -> Union[int, float]:
        """
        居中对齐的起始位置
        :param start_x:
        :param end_x:
        :param str_name:
        :return:
        """
        mid_xpath = (end_x + start_x) / 2
        strname_width = self.text_width(str_name)
        xpath = mid_xpath - strname_width / 2
        return xpath

    def draw_watermark(self, original_image: Image.Image) -> Image.Image:
        """
        绘制水印
        """
        if not self.image['watermark']['enable']:
            return original_image
        watermark = self.image.get('watermark', {})
        watermark_text = watermark['text']
        font = ImageFont.truetype(self.config.getFont(), int(watermark['font_size']))
        text_image = Image.new('RGBA', font.getsize(watermark_text), (255, 255, 255, 0))
        text_draw = ImageDraw.Draw(text_image)

        rgb = ImageColor.getrgb(watermark['color'])
        rgba = (rgb[0], rgb[1], rgb[2], (int(watermark['alpha'])))
        text_draw.text((0, 0), watermark_text, rgba, font=font)

        angle = float(watermark['angle'])
        rotated_text_image = text_image.rotate(angle, expand=True, fillcolor=(0, 0, 0, 0),
                                               resample=Image.BILINEAR)
        watermarks_image = Image.new('RGBA', original_image.size, (255, 255, 255, 0))
        x = original_image.size[0] // 2 - rotated_text_image.size[0] // 2
        row_spacing = int(watermark['row_spacing'])
        if row_spacing < 0:
            row_spacing = 0
        y = int(watermark['start_y'])
        while True:
            watermarks_image.paste(rotated_text_image, (x, y))
            y += rotated_text_image.size[1] + row_spacing
            if y >= original_image.size[1]:
                break

        return Image.alpha_composite(original_image, watermarks_image)

    def draw_background(self) -> Image.Image:
        bkgcfg = self.image.get('background', {})
        B1_color = bkgcfg.get('backgrounds', '#ffffff')
        alphas = bkgcfg.get('alpha', 255)
        B1_rgba = getrgb(B1_color) + (alphas,)
        img = Image.new("RGBA", (self.image['widths'][0], self.image['height']), B1_rgba)
        titlet = bkgcfg.get('testtitle', '#EAEAEA')
        titlet_alpha = getrgb(titlet) + (alphas,)
        bkg = Image.new('RGBA', (self.image['widths'][0], self.image['linespace'] * 2), titlet_alpha)  # 首尾部填充
        img.paste(bkg, (0, 0))
        img.paste(bkg, (0, self.image['height'] - self.image['linespace'] * 2))
        return img

    def draw_info(self, idraw: Union[ImageDraw.ImageDraw, Pilmoji]) -> str:
        """
        绘制标题栏和结尾栏信息
        """
        _width = self.image['widths'][0]
        _height = self.image['height']
        _title = f"{self.image['title']} - 连通性测试"
        _wtime = self.image['wtime']
        _sort = self.image['sort']
        _filter_include = self.image['filter_include']
        _filter_exclude = self.image['filter_exclude']
        emoji_time = get_clock_emoji()
        _export_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        system_timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        _default_slavename = self.config.getSlaveconfig().get('default-slave', {}).get('comment', 'Local')
        _slavename = self.allinfo.pop('slave', {}).get('comment', _default_slavename)
        footer = f"📊版本:{__version__}  后端: {_slavename}  排序: {_sort}   " + \
                 f"过滤器: {_filter_include} <-> {_filter_exclude}"
        footer2 = f"{emoji_time}测试时间: {_export_time} ({system_timezone}) 总共耗时: {_wtime}s 测试结果仅供参考,以实际情况为准"

        idraw.text((self.get_mid(0, _width, _title), 3), _title, font=self._font, fill=(0, 0, 0))  # 标题
        if isinstance(idraw, Pilmoji):
            idraw.text((10, _height - (self.image['linespace'] - 4) * 2), footer, font=self._font, fill=(0, 0, 0),
                       emoji_position_offset=(0, 6))  # 版本信息
            idraw.text((10, _height - (self.image['linespace'] - 5)), footer2, font=self._font, fill=(0, 0, 0),
                       emoji_position_offset=(0, 6))  # 测试时间
        else:
            idraw.text((10, _height - (self.image['linespace'] - 4) * 2), footer, font=self._font, fill=(0, 0, 0))
            idraw.text((10, _height - (self.image['linespace'] - 5)), footer2, font=self._font, fill=(0, 0, 0))
        return _export_time.replace(':', '-')

    def draw_label(self, idraw):
        """
        绘制标签,效果图：
        ---------------------------
        |节点名称|节点类型|HTTP(S)延迟...|
        --------------------------
        """
        _nodename_width = self.image['widths'][1]
        _info_list_width = list(self.image['widths'][2])
        _key_list = self.get_key_list()
        text_list = [('序号', 20), ('节点名称', self.get_mid(100, _nodename_width + 100, '节点名称'))]
        start_x = 100 + _nodename_width
        for i, info_width in enumerate(_info_list_width):
            end_x = start_x + info_width
            text_list.append((_key_list[i], self.get_mid(start_x, end_x, _key_list[i])))
            start_x = end_x
        for text, x in text_list:
            idraw.text((x, self.image['linespace'] + self.image['ctofs'] - 5), text, fill=(0, 0, 0))

    def draw_line(self, idraw):
        # 绘制横线
        _lspace = self.image['linespace']
        _image_width = self.image['widths'][0]
        _nodename_width = self.image['widths'][1]
        _info_list_width = list(self.image['widths'][2])
        for t in range(self.nodenum + 3):
            idraw.line([(0, _lspace * (t + 1)), (_image_width, _lspace * (t + 1))], fill="#e1e1e1", width=2)
        # 绘制竖线
        idraw.line([(100, _lspace), (100, _lspace * 2)], fill="#EAEAEA", width=2)
        start_x = 100 + _nodename_width
        for i in _info_list_width:
            x = start_x
            end = start_x + i
            idraw.line([(x, _lspace), (x, self.image['height'] - _lspace * 2)], fill="#EAEAEA", width=2)
            start_x = end

    def draw_content(self, draw: Union[Pilmoji, ImageDraw.ImageDraw], xy: tuple, ct: str, fill=(0, 0, 0)):
        """
        绘制具体内容
        ct: content内容
        """
        try:
            if isinstance(draw, Pilmoji):
                # 自定义emoji源可能出错，所以捕捉了异常
                draw.text(xy, ct, fill, font=self._font, emoji_position_offset=(0, 6))
            else:
                draw.text(xy, ct, fill, font=self._font)
        except Exception as e:
            logger.warning("绘图错误:" + str(e))
            draw.text(xy, ct, fill, font=self._font)

    def draw_block(self, img: Image.Image, index: int, _nodename_width, _key_list, _info_list_width):
        """
        绘制颜色块
        """
        t = index
        ls = self.image['linespace']
        colorvalue = self.image['colorvalue']
        interval = self.image['interval']
        alphas = self.image['alphas']
        delay_end_color = self.image['end_color']
        c_block = self.c_block
        c_alpha = self.c_alpha
        c_end_color = self.c_end_color
        width = 100 + _nodename_width
        for i, t1 in enumerate(_key_list):
            content = self.info[t1][t]
            if "RTT延迟" == t1 or "HTTP(S)延迟" == t1:
                rtt = float(content[:-2])
                # 使用了二分法（bisection）算法，它的时间复杂度是 O(log n)。j 这里是确定rtt比interval中的哪个值大
                # bisect.bisect_right(interval, rtt) 减去1 就拿到了指定的值，最后max函数防止j为负
                j = max(bisect.bisect_right(interval, rtt) - 1, 0)
                block = c_block_grad((_info_list_width[i], ls), color_value=colorvalue[j], end_color=delay_end_color[j],
                                     alpha=alphas[j])
                img.alpha_composite(block, (width, ls * (t + 2)))
            elif '国创' in content or '海外' in content:
                block = c_block_grad((_info_list_width[i], ls), color_value=c_block['海外'], end_color=c_end_color['海外'],
                                     alpha=c_alpha['海外'])
                img.alpha_composite(block, (width, ls * (t + 2)))
            elif ('解锁' in content or '允许' in content) and '待' not in content:
                block = c_block_grad((_info_list_width[i], ls), color_value=c_block['成功'], end_color=c_end_color['成功'],
                                     alpha=c_alpha['成功'])
                img.alpha_composite(block, (width, ls * (t + 2)))
            elif '失败' in content or '禁止' in content or '不' in content or '无' in content:
                block = c_block_grad((_info_list_width[i], ls), color_value=c_block['失败'], end_color=c_end_color['失败'],
                                     alpha=c_alpha['失败'])
                img.alpha_composite(block, (width, ls * (t + 2)))
            elif '待解' in content or '送中' in content:
                block = c_block_grad((_info_list_width[i], ls), color_value=c_block['待解锁'],
                                     end_color=c_end_color['待解锁'], alpha=c_alpha['待解锁'])
                img.alpha_composite(block, (width, ls * (t + 2)))
            elif 'N/A' in content:
                block = c_block_grad((_info_list_width[i], ls), color_value=c_block['N/A'],
                                     end_color=c_end_color['N/A'], alpha=c_alpha['N/A'])
                img.alpha_composite(block, (width, ls * (t + 2)))
            elif 'Low' in content:
                block = c_block_grad((_info_list_width[i], ls), color_value=c_block['low'],
                                     end_color=c_end_color['low'], alpha=c_alpha['low'])
                img.alpha_composite(block, (width, ls * (t + 2)))
            elif 'Medium' in content:
                block = c_block_grad((_info_list_width[i], ls), color_value=c_block['medium'],
                                     end_color=c_end_color['medium'],
                                     alpha=c_alpha['medium'])
                img.alpha_composite(block, (width, ls * (t + 2)))
            elif 'High' in content and 'Very' not in content:
                block = c_block_grad((_info_list_width[i], ls), color_value=c_block['high'],
                                     end_color=c_end_color['high'], alpha=c_alpha['high'])
                img.alpha_composite(block, (width, ls * (t + 2)))
            elif 'Very' in content:
                block = c_block_grad((_info_list_width[i], ls), color_value=c_block['veryhigh'],
                                     end_color=c_end_color['veryhigh'],
                                     alpha=c_alpha['veryhigh'])
                img.alpha_composite(block, (width, ls * (t + 2)))
            elif '超时' in content or '连接错误' in content:
                block = c_block_grad((_info_list_width[i], ls), color_value=c_block['警告'], end_color=c_end_color['警告'],
                                     alpha=c_alpha['警告'])
                img.alpha_composite(block, (width, ls * (t + 2)))
            elif '未知' in content:
                block = c_block_grad((_info_list_width[i], ls), color_value=c_block['未知'], end_color=c_end_color['未知'],
                                     alpha=c_alpha['未知'])
                img.alpha_composite(block, (width, ls * (t + 2)))
            elif '自制' in content:
                block = c_block_grad((_info_list_width[i], ls), color_value=c_block['自制'], end_color=c_end_color['自制'],
                                     alpha=c_alpha['自制'])
                img.alpha_composite(block, (width, ls * (t + 2)))
            elif '货币' in content:
                block = c_block_grad((_info_list_width[i], ls), color_value=c_block['成功'], end_color=c_end_color['成功'],
                                     alpha=c_alpha['成功'])
                img.alpha_composite(block, (width, ls * (t + 2)))
            else:
                pass
            width += _info_list_width[i]

    @logger.catch()
    def draw(self, debug=False):
        """
        绘制图像主要函数
        debug为True时会额外输出图片到桌面环境窗口
        """
        ls = self.image['linespace']
        ctofs = self.image['ctofs'] - 5  # 行间距改变时的补偿偏移量,Compensation offsets
        _nodename_width = self.image['widths'][1]
        _info_list_width = list(self.image['widths'][2])
        _key_list = self.get_key_list()

        img = self.draw_background()  # 1.首先绘制背景图
        idraw = ImageDraw.Draw(img)
        idraw.font = self._font  # 设置字体，之后就不用一直在参数里传入字体实例啦
        pilmoji = Pilmoji(img, source=self.emoji_source)  # emoji表情修复，emoji必须在参数手动指定字体。

        _export_time = self.draw_info(pilmoji)  # 2.绘制标题栏与结尾栏，返回输出图片的时间,文件动态命名。

        self.draw_label(idraw)  # 3.绘制标签

        # 在一个大循环里绘制，主要思路是按行绘制
        for t in range(self.nodenum):
            # 序号
            self.draw_content(idraw, (self.get_mid(0, 100, str(t + 1)), ls * (t + 2) + ctofs), str(t + 1))
            # 节点名称
            self.draw_content(pilmoji, (110, ls * (t + 2) + ctofs), self.basedata[t])
            # 绘制颜色块
            self.draw_block(img, t, _nodename_width, _key_list, _info_list_width)
            # 其他文本内容
            width = 100 + _nodename_width
            for i, t2 in enumerate(_key_list):
                x = self.get_mid(width, width + _info_list_width[i], self.info[t2][t])
                self.draw_content(idraw, (x, ls * (t + 2) + ctofs), self.info[t2][t])
                width += _info_list_width[i]

        self.draw_line(idraw)  # 绘制线条
        img = self.draw_watermark(img)  # 绘制水印
        if debug:
            img.show("debug image view")
        else:
            img.save(r"./results/{}.png".format(_export_time))
        print(_export_time)
        return _export_time, img.size


class ExportSpeed2(ExportCommon):
    """
    绘制速度图
    """

    def __init__(self, primarykey: Union[list, tuple], allinfo: dict):
        self.speedblock_width = 20
        super().__init__(primarykey, allinfo)
        self.image['traffic'] = "%.1f" % self.allinfo.pop('消耗流量', 0)
        self.image['thread'] = str(self.allinfo.pop('线程', ''))
        self.speedcolor = self.color.get('speed', [])

    def draw_info(self, idraw) -> str:
        """
        绘制标题栏和结尾栏信息
        """
        _width = self.image['widths'][0]
        _height = self.image['height']
        _title = f"{self.image['title']} - 速度测试"
        _wtime = self.image['wtime']
        _sort = self.image['sort']
        _filter_include = self.image['filter_include']
        _filter_exclude = self.image['filter_exclude']
        _export_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        _slavename = self.allinfo.pop('slave', {}).get('comment', 'Local')
        footer = f"后端: {_slavename}  耗时: {_wtime}s  消耗流量: {self.image['traffic']}MB   " \
                 f"线程: {self.image['thread']}  过滤器: {_filter_include} <-> {_filter_exclude}"
        footer2 = f"版本:{__version__}  测试时间: {_export_time}  测试结果仅供参考,以实际情况为准"
        idraw.text((self.get_mid(0, _width, _title), 3), _title, fill=(0, 0, 0))  # 标题
        idraw.text((10, _height - 112), footer, fill=(0, 0, 0))  # 版本信息
        idraw.text((10, _height - 55), footer2, fill=(0, 0, 0))  # 测试时间
        return _export_time.replace(':', '-')

    def draw_block(self, img: Image.Image, index: int, _nodename_width, _key_list, _info_list_width):
        """
        绘制颜色块
        """
        t = index
        colorvalue = self.image['colorvalue']
        interval = self.image['interval']
        alphas = self.image['alphas']
        end_color = self.image['end_color']
        width = 100 + _nodename_width
        for i, t1 in enumerate(_key_list):
            if "RTT延迟" == t1 or "HTTP(S)延迟" == t1:
                rtt = float(self.info[t1][t][:-2])
                if interval[0] < rtt < interval[1]:
                    block = c_block_grad((_info_list_width[i], 60), color_value=colorvalue[0], end_color=end_color[0],
                                         alpha=alphas[0])
                    img.alpha_composite(block, (width, 60 * (t + 2)))
                elif interval[1] <= rtt < interval[2]:
                    block = c_block_grad((_info_list_width[i], 60), color_value=colorvalue[1], end_color=end_color[1],
                                         alpha=alphas[1])
                    img.alpha_composite(block, (width, 60 * (t + 2)))
                elif interval[2] <= rtt < interval[3]:
                    block = c_block_grad((_info_list_width[i], 60), color_value=colorvalue[2], end_color=end_color[2],
                                         alpha=alphas[2])
                    img.alpha_composite(block, (width, 60 * (t + 2)))
                elif interval[3] <= rtt < interval[4]:
                    block = c_block_grad((_info_list_width[i], 60), color_value=colorvalue[3], end_color=end_color[3],
                                         alpha=alphas[3])
                    img.alpha_composite(block, (width, 60 * (t + 2)))
                elif interval[4] <= rtt < interval[5]:
                    block = c_block_grad((_info_list_width[i], 60), color_value=colorvalue[4], end_color=end_color[4],
                                         alpha=alphas[4])
                    img.alpha_composite(block, (width, 60 * (t + 2)))
                elif interval[5] <= rtt < interval[6]:
                    block = c_block_grad((_info_list_width[i], 60), color_value=colorvalue[5], end_color=end_color[5],
                                         alpha=alphas[5])
                    img.alpha_composite(block, (width, 60 * (t + 2)))
                elif interval[6] <= rtt:
                    block = c_block_grad((_info_list_width[i], 60), color_value=colorvalue[6], end_color=end_color[6],
                                         alpha=alphas[6])
                    img.alpha_composite(block, (width, 60 * (t + 2)))
                elif rtt == 0:
                    block = c_block_grad((_info_list_width[i], 60), color_value=colorvalue[7], end_color=end_color[7],
                                         alpha=alphas[7])
                    img.alpha_composite(block, (width, 60 * (t + 2)))

    def draw_delay(self, img, t1: str, t: int, info_list_length, speedblock_height):
        pass
        # speedvalue = float(self.info[t1][t][:-2])
        # if "MB" in self.info[t1][t]:
        #     block = color_block((info_list_length[i], speedblock_height), color_value=get_color(speedvalue),
        #                         alpha=get_alphas(speedvalue))
        #     img.alpha_composite(block, (width, speedblock_height * (t + 2)))
        # elif "KB" in self.info[t1][t] and float(self.info[t1][t][:-2]) > 0:
        #     speedvalue = float(self.info[t1][t][:-2])
        #     block = color_block((info_list_length[i], speedblock_height), color_value=get_color(1),
        #                         alpha=get_alphas(1))
        #     img.alpha_composite(block, (width, speedblock_height * (t + 2)))
        # else:
        #     speedvalue = float(self.info[t1][t][:-2])
        #     block = color_block((info_list_length[i], speedblock_height), color_value=get_color(speedvalue),
        #                         alpha=get_alphas(speedvalue))
        #     img.alpha_composite(block, (width, speedblock_height * (t + 2)))

    def key_width_list(self):
        """
        得到所有测试项列的大小
        :return: list
        """
        speedblock_width = self.speedblock_width
        key_list = self.get_key_list()  # 得到每个测试项绘图的大小[100,80]
        width_list = []
        for i in key_list:
            key_width = self.text_width(i)  # 键的长度
            if i == '每秒速度':
                key_width += 40
                speedblock_count = max(len(lst) for lst in self.info[i]) if self.info[i] else 0
                if speedblock_count > 0:
                    speedblock_total_width = speedblock_count * speedblock_width
                    if speedblock_total_width >= key_width:
                        max_width = speedblock_total_width
                    else:
                        speedblock_width = math.ceil(key_width / speedblock_count)
                        max_width = speedblock_count * speedblock_width
                else:
                    max_width = key_width
            else:
                value_width = self.text_maxwidth(self.info[i])  # 键所对应值的长度
                max_width = max(key_width, value_width)
                max_width += 40
            width_list.append(max_width)
        self.speedblock_width = speedblock_width
        return width_list  # 测试项列的大小

    @logger.catch()
    def draw(self):
        img = self.draw_background()  # 首先绘制背景图
        idraw = ImageDraw.Draw(img)
        idraw.font = self._font  # 设置字体，之后就不用一直在参数里传入字体实例啦
        pilmoji = Pilmoji(img, source=self.emoji_source)  # emoji表情修复，emoji必须在参数手动指定字体。

        _nodename_width = self.image['widths'][1]
        _info_list_width = list(self.image['widths'][2])
        _key_list = self.get_key_list()
        _export_time = self.draw_info(idraw)  # 绘制标题栏与结尾栏，返回输出图片的时间,文件动态命名。

        self.draw_label(idraw)  # 绘制标签

        for t in range(self.nodenum):
            # 序号
            self.draw_content(idraw, (self.get_mid(0, 100, str(t + 1)), 60 * (t + 2) + 6), str(t + 1))
            # 节点名称
            self.draw_content(pilmoji, (110, 60 * (t + 2) + 5), self.basedata[t])
            # 绘制颜色块
            self.draw_block(img, t, _nodename_width, _key_list, _info_list_width)
        self.draw_line(idraw)  # 绘制线条
        img = self.draw_watermark(img)  # 绘制水印
        # img.show("coffee")
        img.save(r"./results/{}.png".format(_export_time))
        print(_export_time)
        return _export_time


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
        self.front_size = 38
        self.config = ConfigManager()

        self.emoji = self.config.config.get('emoji', {}).get('enable', True)  # 是否启用emoji，若否，则在输出图片时emoji将无法正常显示
        emoji_source_name = self.config.config.get('emoji', {}).get('emoji-source', "TwemojiLocalSource")
        if emoji_source_name in emoji_source.__all__:
            self.emoji_source = getattr(emoji_source, emoji_source_name)
        else:
            self.emoji_source = emoji_source.TwemojiLocalSource
        self.color = self.config.getColor()
        self.image_config = self.config.config.get('image', {})
        self.delay_color = self.color.get('delay', [])
        self.__font = ImageFont.truetype(self.config.getFont(), self.front_size)
        self.title = self.image_config.get('title', 'FullTclash')
        self.background = self.image_config.get('background', {})
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
                self.watermark[key] = watermark_default_config.get(key)

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
    def alphas(self):
        alphas_list = []
        for c in self.delay_color:
            alphas_list.append(c.get('alpha', 255))
        while len(alphas_list) < 8:
            alphas_list.append(255)
        if len(alphas_list) > 8:
            return alphas_list[:8]
        else:
            return alphas_list

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
        return (self.nodenum + 4) * 60

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
        draw = ImageDraw.Draw(Image.new("RGBA", (1, 1), (255, 255, 255, 255)))
        textSize = int(draw.textlength(text, font=font))
        # textSize = draw.textsize(text, font=font)[0]
        return textSize

    def text_maxwidth(self, strlist: list):
        """
        得到列表中最长字符串的绘图长度

        :param strlist:
        :return: int
        """
        font = self.__font
        draw = ImageDraw.Draw(Image.new("RGBA", (1, 1), (255, 255, 255, 255)))
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
            max_width = max_width + 60
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
        watermark_text = self.watermark['text']
        font = ImageFont.truetype(self.config.getFont(), int(self.watermark['font_size']))
        text_image = Image.new('RGBA', font.getsize(watermark_text), (255, 255, 255, 0))
        text_draw = ImageDraw.Draw(text_image)

        rgb = ImageColor.getrgb(self.watermark['color'])
        rgba = (rgb[0], rgb[1], rgb[2], (int(self.watermark['alpha'])))
        text_draw.text((0, 0), watermark_text, rgba, font=font)

        angle = float(self.watermark['angle'])
        rotated_text_image = text_image.rotate(angle, expand=True, fillcolor=(0, 0, 0, 0),
                                               resample=Image.BILINEAR)
        watermarks_image = Image.new('RGBA', original_image.size, (255, 255, 255, 0))

        x = original_image.size[0] // 2 - rotated_text_image.size[0] // 2
        row_spacing = int(self.watermark['row_spacing'])
        if row_spacing < 0:
            row_spacing = 0
        y = int(self.watermark['start_y'])
        while True:
            watermarks_image.paste(rotated_text_image, (x, y))
            y += rotated_text_image.size[1] + row_spacing
            if y >= original_image.size[1]:
                break

        return Image.alpha_composite(original_image, watermarks_image)


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
        self.wtime = self.info.pop('wtime', "未知")
        self.nodenum = len(self.basedata)
        self.front_size = 38
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
        heightlist = (self.nodenum + 4) * 60
        return heightlist

    def text_width(self, text: str):
        """
        得到字符串在图片中的绘图长度

        :param text: 文本内容
        :return: int
        """
        font = self.__font
        draw = ImageDraw.Draw(Image.new("RGBA", (1, 1), (255, 255, 255, 255)))
        textSize = int(draw.textlength(text, font=font))
        # textSize = draw.textsize(text, font=font)[0]
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
        self.background = self.image_config.get('background', {})
        T_color = self.background.get('ins', '#ffffff')
        alphas = self.background.get('alpha', 255)
        T_color_alpha = tuple(int(T_color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) + (alphas,)
        img = Image.new("RGBA", (image_width, image_height), T_color_alpha)
        pilmoji = Pilmoji(img, source=self.emoji_source)  # emoji表情修复
        # 绘制色块
        titlea = self.background.get('topotitle', '#EAEAEA')
        bkg = Image.new('RGBA', (image_width, 120), titlea)  # 首尾部填充
        img.paste(bkg, (0, 0))
        img.paste(bkg, (0, image_height - 120))
        idraw = ImageDraw.Draw(img)
        # 绘制标题栏与结尾栏
        export_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())  # 输出图片的时间,文件动态命名
        list1 = [f"{self.title} - 节点拓扑分析", "版本:{} 总共耗时: {}s".format(__version__, self.wtime),
                 "测试时间: {}  测试结果仅供参考".format(export_time)]
        export_time = export_time.replace(':', '-')
        title = list1[0]
        idraw.text((self.get_mid(0, image_width, title), 1), title, font=fnt, fill=(0, 0, 0))  # 标题

        if self.emoji:
            pilmoji.text((10, image_height - 120), text=list1[1], font=fnt, fill=(0, 0, 0),
                         emoji_position_offset=(0, 6))
        else:
            idraw.text((10, image_height - 120), text=list1[1], font=fnt, fill=(0, 0, 0))  # 版本信息
        idraw.text((10, image_height - 60), text=list1[2], font=fnt, fill=(0, 0, 0))  # 测试时间
        # 绘制标签
        idraw.text((20, 60), '序号', font=fnt, fill=(0, 0, 0))  # 序号
        start_x = 100
        m = 0  # 记录测试项数目
        for i in info_list_length:
            x = start_x
            end = start_x + i
            idraw.text((self.get_mid(x, end, key_list[m]), 60), key_list[m], font=fnt, fill=(0, 0, 0))
            start_x = end
            m = m + 1
        # 内容填充
        # cu = self.info.pop('簇', [1 for _ in range(self.nodenum)])
        for t in range(self.nodenum):
            # 序号
            idraw.text((self.get_mid(0, 100, str(t + 1)), 60 * (t + 2)), text=str(t + 1), font=fnt, fill=(0, 0, 0))
            width = 100
            i = 0
            for t1 in key_list:
                if t1 == "组织":
                    idraw.text((width + 10, (t + 2) * 60),
                               self.info[t1][t],
                               font=fnt, fill=(0, 0, 0))
                elif t1 == "AS编号":
                    idraw.text((self.get_mid(width, width + info_list_length[i], self.info[t1][t]), (t + 2) * 60),
                               self.info[t1][t],
                               font=fnt, fill=(0, 0, 0))
                elif t1 == "栈":
                    try:
                        if self.emoji:
                            if self.info[t1][t] == "4":
                                img_to_paste = Image.open("resources/image/4.png")

                                img_to_paste = img_to_paste.resize((25, 25))

                                paste_location = (width + int((40 - img_to_paste.size[0]) / 2) + 30,
                                                  (t + 2) * 60 + int((60 - img_to_paste.size[1]) / 2))

                                img.paste(img_to_paste, paste_location)

                            elif self.info[t1][t] == "6":
                                img_to_paste = Image.open("resources/image/6.png")

                                img_to_paste = img_to_paste.resize((25, 25))

                                paste_location = (width + int((40 - img_to_paste.size[0]) / 2) + 30,
                                                  (t + 2) * 60 + int((60 - img_to_paste.size[1]) / 2))

                                img.paste(img_to_paste, paste_location)
                            elif self.info[t1][t] == "46":
                                img_to_paste_4 = Image.open("resources/image/4.png")
                                img_to_paste_4 = img_to_paste_4.resize((25, 25))

                                img_to_paste_6 = Image.open("resources/image/6.png")
                                img_to_paste_6 = img_to_paste_6.resize((25, 25))

                                paste_location_4 = (width + int((40 - img_to_paste_4.size[0]) / 2) + 20,
                                                    (t + 2) * 60 + int((60 - img_to_paste_4.size[1]) / 2))

                                paste_location_6 = (width + int((40 - img_to_paste_6.size[0]) / 2) + 60,
                                                    (t + 2) * 60 + int((60 - img_to_paste_6.size[1]) / 2))

                                img.paste(img_to_paste_4, paste_location_4)
                                img.paste(img_to_paste_6, paste_location_6)

                            elif self.info[t1][t] == "64":
                                img_to_paste_4 = Image.open("resources/image/4.png")
                                img_to_paste_4 = img_to_paste_4.resize((25, 25))

                                img_to_paste_6 = Image.open("resources/image/6.png")
                                img_to_paste_6 = img_to_paste_6.resize((25, 25))

                                paste_location_4 = (width + int((40 - img_to_paste_4.size[0]) / 2) + 20,
                                                    (t + 2) * 60 + int((60 - img_to_paste_4.size[1]) / 2))

                                paste_location_6 = (width + int((40 - img_to_paste_6.size[0]) / 2) + 60,
                                                    (t + 2) * 60 + int((60 - img_to_paste_6.size[1]) / 2))

                                img.paste(img_to_paste_6, paste_location_4)
                                img.paste(img_to_paste_4, paste_location_6)
                            else:
                                img_to_paste = Image.open("resources/image/no.png")

                                img_to_paste = img_to_paste.resize((25, 25))

                                paste_location = (width + int((40 - img_to_paste.size[0]) / 2) + 30,
                                                  (t + 2) * 60 + int((60 - img_to_paste.size[1]) / 2))

                                img.paste(img_to_paste, paste_location)

                        else:
                            idraw.text((width + 40, (t + 2) * 60), self.info[t1][t], font=fnt, fill=(0, 0, 0))
                    except PIL.UnidentifiedImageError:
                        logger.warning("无效符号:" + self.basedata[t])
                        pilmoji2 = Pilmoji(img, source=Twemoji)
                        pilmoji2.text((width + 40, (t + 2) * 60),
                                      self.info[t1][t],
                                      font=fnt, fill=(0, 0, 0), emoji_position_offset=(0, 6))
                    except Exception as e:
                        logger.error(str(e))
                        idraw.text((width + 40, (t + 2) * 60), self.info[t1][t], font=fnt, fill=(0, 0, 0))
                    idraw.line(
                        [(width, (t + 3) * 60), (width + info_list_length[i], (t + 3) * 60)],
                        fill="#e1e1e1", width=2)

                else:
                    idraw.text((self.get_mid(width, width + info_list_length[i], str(self.info[t1][t])), (t + 2) * 60),
                               str(self.info[t1][t]),
                               font=fnt, fill=(0, 0, 0))
                width += info_list_length[i]
                i += 1
        # 绘制横线
        for t in range(self.nodenum + 3):
            idraw.line([(0, 60 * (t + 1)), (image_width, 60 * (t + 1))], fill="#e1e1e1", width=1)
        start_x = 100
        for i in info_list_length:
            x = start_x
            end = start_x + i
            idraw.line([(x, 60), (x, image_height - 120)], fill=(255, 255, 255), width=1)
            start_x = end
        if info2 and nodename:
            img2, image_height2, image_width2 = self.exportTopoOutbound(nodename, info2, img2_width=image_width)
            img3 = Image.new("RGBA", (max(image_width, image_width2), image_height + image_height2 - 120),
                             (255, 255, 255, 255))
            img3.paste(img, (0, 0))
            img3.paste(img2, (0, image_height - 120))

            if self.watermark['enable']:
                img3 = self.draw_watermark(img3.convert("RGBA"))
            print(export_time)
            # img3.show()
            img3.save(r"./results/Topo{}.png".format(export_time.replace(':', '-')))
            return export_time, img3.size
        else:
            if self.watermark['enable']:
                img = self.draw_watermark(img.convert("RGBA"))
            print(export_time)
            img.save(r"./results/Topo{}.png".format(export_time.replace(':', '-')))
            return export_time, img.size

    @logger.catch
    def exportTopoOutbound(self, nodename: list = None, info: dict = None, img2_width: int = None):
        if nodename or info:
            self.__init__(nodename, info)
        _default_slavename = self.config.getSlaveconfig().get('default-slave', {}).get('comment', 'Local')
        slavecomment = self.info.pop('slave', {}).get('comment', _default_slavename)
        fnt = self.__font
        image_width, info_list_length = self.get_width(compare=img2_width)
        image_height = self.get_height()
        key_list = self.get_key_list()
        self.background = self.image_config.get('background', {})
        O_color = self.background.get('outs', '#ffffff')
        alphas = self.background.get('alpha', 255)
        O_color_alpha = tuple(int(O_color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) + (alphas,)
        img = Image.new("RGBA", (image_width, image_height), O_color_alpha)
        pilmoji = Pilmoji(img, source=self.emoji_source)  # emoji表情修复
        # 绘制色块
        titlea = self.background.get('topotitle', '#EAEAEA')
        bkg = Image.new('RGBA', (image_width, 120), titlea)  # 首尾部填充
        img.paste(bkg, (0, 0))
        img.paste(bkg, (0, image_height - 120))
        idraw = ImageDraw.Draw(img)
        image_conf = {'delay_color': self.color.get('out_color', [])}
        alphas = []
        color_topo = []
        end_color = []
        if not image_conf['delay_color']:
            color_topo = ["#FFF3F3", '#FAF3FF', '#FFF3FC', '#F3F5FF', '#FFFBF3', '#FBFFF3', '#F3FFFF', '#F3FFF4']
        else:
            delay_color = image_conf['delay_color']
            for c in delay_color:
                alphas.append(c.get('alpha', 255))
                color_topo.append(c.get('value', '#EDF7FF'))
                if "end_color" in c:
                    end_color.append(c.get('end_color', '#EDF7FF'))
                else:
                    end_color.append(c.get('value', '#EDF7FF'))
        # 绘制标题栏与结尾栏
        fail = self.info.get('地区', 0)
        entrances = self.info.get('入口')
        max_entrance = max(entrances) if entrances else 0
        cuk = len(fail)

        emoji_time = get_clock_emoji()
        export_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # 输出图片的时间,文件动态命名
        system_timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        tips = "测试结果仅供参考，以实际情况为准，簇代表落地复用。"
        list1 = ["出口分析", f"📊版本:{__version__}  后端:{slavecomment}  概要:{max_entrance}->{cuk}",
                 f"{emoji_time}测试时间: {export_time}({system_timezone}) 总共耗时: {self.wtime}s {tips}"]
        export_time = export_time.replace(':', '-')
        title = list1[0]
        idraw.text((self.get_mid(0, image_width, title), 1), title, font=fnt, fill=(0, 0, 0))  # 标题
        if self.emoji:
            pilmoji.text((10, image_height - 120), text=list1[1], font=fnt, fill=(0, 0, 0),
                         emoji_position_offset=(0, 7))
            pilmoji.text((10, image_height - 60), text=list1[2], font=fnt, fill=(0, 0, 0),
                         emoji_position_offset=(0, 10))
        else:
            idraw.text((10, image_height - 120), text=list1[1], font=fnt, fill=(0, 0, 0))  # 版本信息
            idraw.text((10, image_height - 60), text=list1[2], font=fnt, fill=(0, 0, 0))  # 测试时间
        # 绘制标签
        idraw.text((20, 60), '序号', font=fnt, fill=(0, 0, 0))  # 序号
        start_x = 100
        m = 0  # 记录测试项数目
        for i in info_list_length:
            x = start_x
            end = start_x + i
            idraw.text((self.get_mid(x, end, key_list[m]), 60), key_list[m], font=fnt, fill=(0, 0, 0))
            start_x = end
            m = m + 1
        ct = [item for item in self.info.get('入口')]
        cu = [item for item in self.info.get('簇')]
        bh = [item for item in self.info.get('AS编号')]
        zz = [item for item in self.info.get('组织')]
        dq = [item for item in self.info.get('地区')]

        # 绘制横线
        # for t in range(self.nodenum + 3):
        #     idraw.line([(0, 40 * (t + 1)), (image_width, 40 * (t + 1))], fill="#e1e1e1", width=2)
        # 内容填充

        cu_offset = 0
        cu_offset2 = 0
        ct_offset = 0
        ct_offset2 = 0
        bh_offset = 0
        bh_offset2 = 0
        zz_offset = 0
        zz_offset2 = 0
        dq_offset = 0
        dq_offset2 = 0

        min_ct = []  # 入口统计列表
        min_bh = []  # AS编号统计列表
        min_zz = []  # 组织统计列表
        min_dq = []  # 地区统计列表

        last_index = 0
        last_index2 = 0
        last_index3 = 0
        last_index4 = 0

        new_bh = [bh[0]]  # 新的AS编号列表
        new_ct = [ct[0]]  # 新的入口列表
        new_zz = [zz[0]]  # 新的组织列表
        new_dq = [dq[0]]  # 新的地区列表

        for i in range(1, len(ct)):
            if ct[i] != ct[i - 1]:
                new_ct.append(ct[i])
                min_ct.append(i - last_index)
                last_index = i
        min_ct.append(len(ct) - last_index)

        for j in range(1, len(bh)):
            if dq[j] != dq[j - 1] or zz[j] != zz[j - 1]:
                new_bh.append(bh[j])
                min_bh.append(j - last_index2)
                last_index2 = j
        min_bh.append(len(bh) - last_index2)

        for k in range(1, len(zz)):
            if dq[k] != dq[k - 1] or zz[k] != zz[k - 1]:
                new_zz.append(zz[k])
                min_zz.append(k - last_index3)
                last_index3 = k
        min_zz.append(len(zz) - last_index3)

        for f in range(1, len(dq)):
            if dq[f] != dq[f - 1] or zz[f] != zz[f - 1]:
                new_dq.append(dq[f])
                min_dq.append(f - last_index4)
                last_index4 = f
        min_dq.append(len(dq) - last_index4)

        s = 0
        for t in range(self.nodenum):
            if t < len(new_ct):
                if min_ct[t] > 1:
                    ct_offset2 += min_ct[t] - 1

            width = 100
            i = 0

            for t2 in key_list:
                if t2 == "入口":
                    if t < len(min_ct):
                        temp = min_ct[t]
                        y = ((t + 2) * 60 + (t + 2) * 60 + (60 * (temp - 1))) / 2 + ct_offset * 60
                        idraw.text((self.get_mid(width, width + info_list_length[i], str(new_ct[t])), y),
                                   str(new_ct[t]),
                                   font=fnt, fill=(0, 0, 0))

                        if min_ct[t] > 1:
                            ct_offset += min_ct[t] - 1
                        idraw.line([(width, (t + 3 + ct_offset2) * 60),
                                    (width + info_list_length[i], (t + 3 + ct_offset2) * 60)],
                                   fill="#e1e1e1", width=2)
            s += 1
            if s >= len(color_topo):
                s = 0
        for t in range(self.nodenum):
            # 序号
            idraw.text((self.get_mid(0, 100, str(t + 1)), 60 * (t + 2)), text=str(t + 1), font=fnt, fill=(0, 0, 0))
            idraw.line([(0, 60 * (t + 3)), (100, 60 * (t + 3))], fill="#e1e1e1", width=2)
            width = 100
            i = 0

            if t < len(cu):
                if cu[t] > 1:
                    cu_offset2 += cu[t] - 1
            if t < len(new_bh):
                if min_bh[t] > 1:
                    bh_offset2 += min_bh[t] - 1
            if t < len(new_zz):
                if min_zz[t] > 1:
                    zz_offset2 += min_zz[t] - 1
            if t < len(new_dq):
                if min_dq[t] > 1:
                    dq_offset2 += min_dq[t] - 1

            for t1 in key_list:

                if t1 == "AS编号":
                    if t < len(min_bh):
                        temp = min_bh[t]
                        y = ((t + 2) * 60 + (t + 2) * 60 + (60 * (temp - 1))) / 2 + bh_offset * 60
                        idraw.text(((self.get_mid(width, width + info_list_length[i],
                                                  str(new_bh[t]))), y), str(new_bh[t]), font=fnt, fill=(0, 0, 0))
                        idraw.line([(width, (t + 3 + bh_offset2) * 60),
                                    (width + info_list_length[i], (t + 3 + bh_offset2) * 60)],
                                   fill="#e1e1e1", width=2)
                        if min_bh[t] > 1:
                            bh_offset += min_bh[t] - 1
                elif t1 == "地区":
                    if t < len(min_dq):
                        temp = min_dq[t]
                        y = ((t + 2) * 60 + (t + 2) * 60 + (60 * (temp - 1))) / 2 + dq_offset * 60
                        idraw.text(((self.get_mid(width, width + info_list_length[i],
                                                  str(new_dq[t]))), y), str(new_dq[t]), font=fnt, fill=(0, 0, 0))
                        idraw.line([(width, (t + 3 + dq_offset2) * 60),
                                    (width + info_list_length[i], (t + 3 + dq_offset2) * 60)],
                                   fill="#e1e1e1", width=2)
                        if min_dq[t] > 1:
                            dq_offset += min_dq[t] - 1
                elif t1 == "组织":
                    if t < len(min_zz):
                        temp = min_zz[t]
                        y = ((t + 2) * 60 + (t + 2) * 60 + (60 * (temp - 1))) / 2 + zz_offset * 60
                        idraw.text((width + 10, y),
                                   str(new_zz[t]),
                                   font=fnt, fill=(0, 0, 0))
                        idraw.line([(width, (t + 3 + zz_offset2) * 60),
                                    (width + info_list_length[i], (t + 3 + zz_offset2) * 60)],
                                   fill="#e1e1e1", width=2)
                        if min_zz[t] > 1:
                            zz_offset += min_zz[t] - 1
                elif t1 == "入口":
                    pass
                elif t1 == "栈":
                    try:
                        if t <= len(dq):
                            if t < len(cu):
                                temp = cu[t]
                                y = ((t + 2) * 60 + (t + 2) * 60 + (60 * (temp - 1))) / 2 + cu_offset * 60
                                x1 = width + (info_list_length[i] - info_list_length[key_list.index("AS编号")]) / 2 + 110
                                if self.info[t1][cu_offset + t] == "4":
                                    img_to_paste = Image.open("resources/image/4.png")

                                    img_to_paste = img_to_paste.resize((25, 25))

                                    paste_location = (int(x1), int(y + 18))

                                    img.paste(img_to_paste, paste_location)
                                    idraw.line([(width, (t + 3 + cu_offset2) * 60),
                                                (width + info_list_length[i], (t + 3 + cu_offset2) * 60)],
                                               fill="#e1e1e1", width=2)

                                elif self.info[t1][cu_offset + t] == "6":
                                    img_to_paste = Image.open("resources/image/6.png")

                                    img_to_paste = img_to_paste.resize((25, 25))

                                    paste_location = (int(x1), int(y + 18))

                                    img.paste(img_to_paste, paste_location)
                                    idraw.line([(width, (t + 3 + cu_offset2) * 60),
                                                (width + info_list_length[i], (t + 3 + cu_offset2) * 60)],
                                               fill="#e1e1e1", width=2)

                                elif self.info[t1][cu_offset + t] == "46":
                                    img_to_paste_4 = Image.open("resources/image/4.png")
                                    img_to_paste_4 = img_to_paste_4.resize((25, 25))

                                    img_to_paste_6 = Image.open("resources/image/6.png")
                                    img_to_paste_6 = img_to_paste_6.resize((25, 25))

                                    paste_location_4 = (int(x1) - 20, int(y + 18))

                                    paste_location_6 = (int(x1) + 20, int(y + 18))

                                    img.paste(img_to_paste_4, paste_location_4)
                                    img.paste(img_to_paste_6, paste_location_6)
                                    idraw.line([(width, (t + 3 + cu_offset2) * 60),
                                                (width + info_list_length[i], (t + 3 + cu_offset2) * 60)],
                                               fill="#e1e1e1", width=2)

                                elif self.info[t1][cu_offset + t] == "N/A":
                                    img_to_paste = Image.open("resources/image/no.png")

                                    img_to_paste = img_to_paste.resize((25, 25))

                                    paste_location = (int(x1), int(y + 18))

                                    img.paste(img_to_paste, paste_location)

                                    idraw.line([(width, (t + 3 + cu_offset2) * 60),
                                                (width + info_list_length[i], (t + 3 + cu_offset2) * 60)],
                                               fill="#e1e1e1", width=2)
                            else:
                                pass
                        else:
                            pass

                    except PIL.UnidentifiedImageError:
                        logger.warning("无效符号:" + self.basedata[t])
                        pilmoji2 = Pilmoji(img, source=Twemoji)
                        pilmoji2.text((width + 40, (t + 2) * 60),
                                      self.info[t1][t],
                                      font=fnt, fill=(0, 0, 0), emoji_position_offset=(0, 6))
                    except Exception as e:
                        logger.error(str(e))
                        idraw.text((width + 40, (t + 2) * 60), self.info[t1][t], font=fnt, fill=(0, 0, 0))

                elif t1 == "簇":
                    if t < len(cu):
                        temp = self.info[t1][t]
                        y = ((t + 2) * 60 + (t + 2) * 60 + (60 * (temp - 1))) / 2 + cu_offset * 60
                        idraw.text((self.get_mid(width, width + info_list_length[i], str(self.info[t1][t])), y),
                                   str(self.info[t1][t]),
                                   font=fnt, fill=(0, 0, 0))
                        if cu[t] > 1:
                            cu_offset += cu[t] - 1
                        idraw.line([(width, (t + 3 + cu_offset2) * 60),
                                    (width + info_list_length[i], (t + 3 + cu_offset2) * 60)],
                                   fill="#e1e1e1", width=2)
                    else:
                        pass
                elif t1 == "节点名称":
                    try:
                        if self.emoji:
                            pilmoji.text((width + 10, (t + 2) * 60),
                                         self.info[t1][t],
                                         font=fnt, fill=(0, 0, 0), emoji_position_offset=(0, 6))
                        else:
                            idraw.text((width + 10, (t + 2) * 60), self.info[t1][t], font=fnt, fill=(0, 0, 0))
                    except PIL.UnidentifiedImageError:
                        logger.warning("无效符号:" + self.basedata[t])
                        pilmoji2 = Pilmoji(img, source=Twemoji)
                        pilmoji2.text((width + 10, (t + 2) * 60),
                                      self.info[t1][t],
                                      font=fnt, fill=(0, 0, 0), emoji_position_offset=(0, 6))
                    except Exception as e:
                        logger.error(str(e))
                        idraw.text((width + 10, (t + 2) * 60), self.info[t1][t], font=fnt, fill=(0, 0, 0))
                    idraw.line(
                        [(width, (t + 3) * 60), (width + info_list_length[i], (t + 3) * 60)],
                        fill="#e1e1e1", width=2)

                else:
                    idraw.text((self.get_mid(width, width + info_list_length[i], str(self.info[t1][t])), (t + 2) * 60),
                               str(self.info[t1][t]),
                               font=fnt, fill=(0, 0, 0))
                width += info_list_length[i]
                i += 1
        idraw.line([(0, 60), (image_width, 60)], fill="#e1e1e1", width=2)
        idraw.line([(0, 120), (image_width, 120)], fill="#e1e1e1", width=2)
        idraw.line([(0, image_height - 60), (image_width, image_height - 60)], fill="#e1e1e1", width=2)
        start_x = 100
        for i in info_list_length:
            x = start_x
            end = start_x + i
            idraw.line([(x, 60), (x, image_height - 120)], fill=(255, 255, 255), width=1)
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
        self.color = self.config.getColor().get('speed', [])
        self.delay_color = self.config.getColor().get('delay', [])
        self.speed_end_colors = self.config.config.get('speed_end_colors_switch', False)
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
        self.nodenum = len(self.basedata) if self.basedata else 0
        self.front_size = 38
        self.__font = ImageFont.truetype(self.config.getFont(), self.front_size)
        self.speedblock_width = 20
        self.slave = info.pop('slave', {})

    def key_value(self):
        """
        得到所有测试项列的大小
        :return: list
        """
        key_list = self.get_key_list()  # 得到每个测试项绘图的大小[100,80]
        width_list = []
        for i in key_list:
            key_width = self.text_width(i)  # 键的长度
            # max_width = 0
            if self.info[i]:
                if i == '每秒速度':
                    key_width += 40
                    speedblock_count = max(len(lst) for lst in self.info[i]) if self.info[i] else 0
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
            else:
                max_width = key_width + 40
            width_list.append(max_width)
        return width_list  # 测试项列的大小

    @property
    def interval(self):
        interval_list = []
        for c in self.delay_color:
            interval_list.append(c.get('label', 0))
        a = list(set(interval_list))  # 去重加排序
        a.sort()
        while len(a) < 8:
            a.append(99999)
        if len(a) > 8:
            return a[:8]
        else:
            return a

    @property
    def intervals(self):
        intervals_list = []
        for c in self.color:
            intervals_list.append(c.get('label', 0))
        a = list(set(intervals_list))  # 去重加排序
        a.sort()
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

    @property
    def colorvalues(self):
        color_list = []
        for c in self.color:
            color_list.append(c.get('value', '#f5f3f2'))
        # while len(color_list) < 7:
        #     color_list.append('#f5f3f2')
        # if len(color_list) > 7:
        #     return color_list[:7]
        # else:
        #     return color_list
        return color_list

    @property
    def alphas(self):
        alphas_list = []
        for c in self.delay_color:
            alphas_list.append(c.get('alpha', 255))
        while len(alphas_list) < 8:
            alphas_list.append(255)
        if len(alphas_list) > 8:
            return alphas_list[:8]
        else:
            return alphas_list

    @property
    def end_colors(self):
        end_colors_list = []
        for c in self.delay_color:
            if self.speed_end_colors:
                end_colors_list.append(c.get('end_color', '#f5f3f2'))
            else:
                end_colors_list.append(c.get('value', '#f5f3f2'))
        while len(end_colors_list) < 8:
            end_colors_list.append('#f5f3f2')
        if len(end_colors_list) > 8:
            return end_colors_list[:8]
        else:
            return end_colors_list

    @property
    def alphaes(self):
        alphaes_list = []
        for c in self.color:
            alphaes_list.append(c.get('alpha', 255))

        return alphaes_list

    @property
    def end_colores(self):
        end_colores_list = []
        for c in self.color:
            if self.speed_end_colors:
                end_colores_list.append(c.get('end_color', "#f5f3f2"))
            else:
                end_colores_list.append(c.get('value', "#f5f3f2"))
        return end_colores_list

    @logger.catch
    def exportImage(self):
        fnt = self.__font
        image_width, nodename_width, info_list_length = self.get_width()
        image_height = self.get_height()
        key_list = self.get_key_list()
        self.background = self.image_config.get('background', {})
        P_color = self.background.get('speedtest', '#ffffff')
        alphas = self.background.get('alpha', 255)
        P_color_alpha = tuple(int(P_color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) + (alphas,)
        img = Image.new("RGBA", (image_width, image_height), P_color_alpha)
        pilmoji = Pilmoji(img, source=self.emoji_source)  # emoji表情修复
        # 绘制背景板
        titles = self.background.get('speedtitle', '#EAEAEA')
        titles_alpha = tuple(int(titles.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) + (alphas,)
        bkg = Image.new('RGBA', (image_width, 120), titles_alpha)  # 首尾部填充
        img.paste(bkg, (0, 0))
        img.paste(bkg, (0, image_height - 120))
        idraw = ImageDraw.Draw(img)
        # 绘制标题栏与结尾栏
        emoji_time = get_clock_emoji()
        export_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # 输出图片的时间,文件动态命名
        system_timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        _default_slavename = self.config.getSlaveconfig().get('default-slave', {}).get('comment', 'Local')
        slavecomment = self.slave.get('comment', _default_slavename)
        list1 = [f"{self.title} - 速度测试",
                 f"📊版本:{__version__}  后端: {slavecomment}  消耗流量: {self.traffic}MB   线程: {self.thread}  " +
                 f"过滤器: {self.filter_include} <-> {self.filter_exclude}",
                 f"{emoji_time}测试时间: {export_time} ({system_timezone}) 总共耗时: {self.wtime}s 测试结果仅供参考,以实际情况为准"]
        export_time = export_time.replace(':', '-')
        title = list1[0]
        idraw.text((self.get_mid(0, image_width, title), 5), title, font=fnt, fill=(0, 0, 0))  # 标题
        if self.emoji:
            pilmoji.text((10, image_height - 112), text=list1[1], font=fnt, fill=(0, 0, 0),
                         emoji_position_offset=(0, 5))
            pilmoji.text((10, image_height - 55), text=list1[2], font=fnt, fill=(0, 0, 0),
                         emoji_position_offset=(0, 5))
        else:
            idraw.text((10, image_height - 112), text=list1[1], font=fnt, fill=(0, 0, 0))  # 版本信息
            idraw.text((10, image_height - 55), text=list1[2], font=fnt, fill=(0, 0, 0))  # 测试时间

        # 绘制标签
        idraw.text((20, 65), '序号', font=fnt, fill=(0, 0, 0))  # 序号
        idraw.text((self.get_mid(100, nodename_width + 100, '节点名称'), 65), '节点名称', font=fnt, fill=(0, 0, 0))  # 节点名称
        start_x = 100 + nodename_width
        m = 0  # 记录测试项数目
        for i in info_list_length:
            x = start_x
            end = start_x + i
            idraw.text((self.get_mid(x, end, key_list[m]), 65), key_list[m], font=fnt, fill=(0, 0, 0))
            start_x = end
            m = m + 1
        # 内容填充
        if self.color:
            colorvalues = self.colorvalues
            intervals = self.intervals
            alphaes = self.alphaes
            end_colores = self.end_colores
        else:
            # 默认值
            colorvalues = ["#f5f3f2", "#beb1aa", "#f6bec8", "#dc6b82", "#c35c5d", "#8ba3c7", "#c8161d"]
            intervals = [0, 1, 5, 10, 20, 60, 100]
            alphaes = [255, 255, 255, 255, 255, 255, 255]
            end_colores = ["#f5f3f2", "#beb1aa", "#f6bec8", "#dc6b82", "#c35c5d", "#8ba3c7", "#c8161d"]

        def get_color(_speedvalue, default_color='#C0C0C0'):
            for _i in reversed(range(len(colorvalues))):
                if _speedvalue >= intervals[_i]:
                    return colorvalues[_i]
            return default_color

        def get_alphas(_speedvalue, default_alphas=255):
            for _i in reversed(range(len(alphaes))):
                if _speedvalue >= intervals[_i]:
                    return alphaes[_i]
            return default_alphas

        def get_end_colors(_speedvalue, default_end_color='#C0C0C0'):
            for _i in reversed(range(len(end_colores))):
                if _speedvalue >= intervals[_i]:
                    return end_colores[_i]
            return default_end_color

        for t in range(self.nodenum):
            # 序号
            idraw.text((self.get_mid(0, 100, str(t + 1)), 60 * (t + 2) + 6), text=str(t + 1), font=fnt, fill=(0, 0, 0))
            # 节点名称
            if self.emoji:
                try:
                    # 自定义emoji源可能出错，所以捕捉了异常
                    pilmoji.text((110, 60 * (t + 2) + 5), text=self.basedata[t], font=fnt, fill=(0, 0, 0),
                                 emoji_position_offset=(0, 6))
                except PIL.UnidentifiedImageError:
                    logger.warning("无效符号:" + self.basedata[t])
                    pilmoji2 = Pilmoji(img, source=Twemoji)
                    pilmoji2.text((110, 60 * (t + 2) + 5), text=self.basedata[t], font=fnt, fill=(0, 0, 0),
                                  emoji_position_offset=(0, 6))
            else:
                idraw.text((110, 60 * (t + 2) + 5), text=self.basedata[t], font=fnt, fill=(0, 0, 0))

            width = 100 + nodename_width + 2
            i = 0
            speedblock_height = 60
            if self.delay_color:
                colorvalue = self.colorvalue
                interval = self.interval
                alphas = self.alphas
                end_color = self.end_colors
            else:
                # 默认值
                colorvalue = ["#f5f3f2", "#beb1aa", "#f6bec8", "#dc6b82", "#c35c5d", "#8ba3c7", "#c8161d", '#8d8b8e']
                interval = [0, 100, 200, 300, 500, 1000, 2000, 99999]
                alphas = [255, 255, 255, 255, 255, 255, 255, 255]
                end_color = ["#f5f3f2", "#beb1aa", "#f6bec8", "#dc6b82", "#c35c5d", "#8ba3c7", "#c8161d", '#8d8b8e']
            # 填充颜色块
            for t1 in key_list:
                if "延迟RTT" == t1 or "HTTP(S)延迟" == t1:
                    rtt = float(self.info[t1][t][:-2])
                    if interval[0] < rtt < interval[1]:
                        block = c_block_grad((info_list_length[i], 60), color_value=colorvalue[0],
                                             end_color=end_color[0], alpha=alphas[0])
                        img.alpha_composite(block, (width, 60 * (t + 2)))
                    elif interval[1] <= rtt < interval[2]:
                        block = c_block_grad((info_list_length[i], 60), color_value=colorvalue[1],
                                             end_color=end_color[1], alpha=alphas[1])
                        img.alpha_composite(block, (width, 60 * (t + 2)))
                    elif interval[2] <= rtt < interval[3]:
                        block = c_block_grad((info_list_length[i], 60), color_value=colorvalue[2],
                                             end_color=end_color[2], alpha=alphas[2])
                        img.alpha_composite(block, (width, 60 * (t + 2)))
                    elif interval[3] <= rtt < interval[4]:
                        block = c_block_grad((info_list_length[i], 60), color_value=colorvalue[3],
                                             end_color=end_color[3], alpha=alphas[3])
                        img.alpha_composite(block, (width, 60 * (t + 2)))
                    elif interval[4] <= rtt < interval[5]:
                        block = c_block_grad((info_list_length[i], 60), color_value=colorvalue[4],
                                             end_color=end_color[4], alpha=alphas[4])
                        img.alpha_composite(block, (width, 60 * (t + 2)))
                    elif interval[5] <= rtt < interval[6]:
                        block = c_block_grad((info_list_length[i], 60), color_value=colorvalue[5],
                                             end_color=end_color[5], alpha=alphas[5])
                        img.alpha_composite(block, (width, 60 * (t + 2)))
                    elif interval[6] <= rtt:
                        block = c_block_grad((info_list_length[i], 60), color_value=colorvalue[6],
                                             end_color=end_color[6], alpha=alphas[6])
                        img.alpha_composite(block, (width, 60 * (t + 2)))
                    elif rtt == 0:
                        block = c_block_grad((info_list_length[i], 60), color_value=colorvalue[7],
                                             end_color=end_color[7], alpha=alphas[7])
                        img.alpha_composite(block, (width, 60 * (t + 2)))
                if t1 == "平均速度" or t1 == "最大速度":
                    if "MB" in self.info[t1][t]:
                        speedvalue = float(self.info[t1][t][:-2])
                        block = c_block_grad((info_list_length[i], speedblock_height),
                                             color_value=get_color(speedvalue), end_color=get_end_colors(speedvalue),
                                             alpha=get_alphas(speedvalue))
                        img.alpha_composite(block, (width, speedblock_height * (t + 2)))
                    elif "KB" in self.info[t1][t] and float(self.info[t1][t][:-2]) > 0:
                        # speedvalue = float(self.info[t1][t][:-2])
                        block = c_block_grad((info_list_length[i], speedblock_height), color_value=get_color(1),
                                             end_color=get_end_colors(1),
                                             alpha=get_alphas(1))
                        img.alpha_composite(block, (width, speedblock_height * (t + 2)))
                    else:
                        speedvalue = float(self.info[t1][t][:-2])
                        block = c_block_grad((info_list_length[i], speedblock_height),
                                             color_value=get_color(speedvalue), end_color=get_end_colors(speedvalue),
                                             alpha=get_alphas(speedvalue))
                        img.alpha_composite(block, (width, speedblock_height * (t + 2)))
                elif t1 == "每秒速度":
                    speedblock_x = width
                    for speedvalue in self.info[t1][t]:
                        max_speed = float(self.info["最大速度"][t][:-2])
                        if max_speed > 0.0:
                            if max_speed < 50:
                                speedblock_ratio_height = int(speedblock_height * speedvalue / 50)
                                if speedblock_ratio_height > speedblock_height:
                                    speedblock_ratio_height = speedblock_height
                                speedblock_y = speedblock_height * (t + 2) + (
                                        speedblock_height - speedblock_ratio_height)

                                block = c_block_grad((self.speedblock_width, speedblock_ratio_height),
                                                     color_value=get_color(speedvalue),
                                                     end_color=get_end_colors(speedvalue), alpha=get_alphas(speedvalue))
                                img.alpha_composite(block, (speedblock_x, speedblock_y))
                            else:
                                speedblock_ratio_height = int(speedblock_height * speedvalue / max_speed)
                                if speedblock_ratio_height > speedblock_height:
                                    speedblock_ratio_height = speedblock_height
                                speedblock_y = speedblock_height * (t + 2) + (
                                        speedblock_height - speedblock_ratio_height)

                                block = c_block_grad((self.speedblock_width, speedblock_ratio_height),
                                                     color_value=get_color(speedvalue),
                                                     end_color=get_end_colors(speedvalue), alpha=get_alphas(speedvalue))
                                img.alpha_composite(block, (speedblock_x, speedblock_y))
                        speedblock_x += self.speedblock_width
                width += info_list_length[i]
                i += 1

            # 填充字符
            width = 100 + nodename_width
            i = 0
            for t2 in key_list:
                if isinstance(self.info[t2][t], str):
                    idraw.text((self.get_mid(width, width + info_list_length[i], self.info[t2][t]), (t + 2) * 60 + 5),
                               self.info[t2][t],
                               font=fnt, fill=(0, 0, 0))
                width += info_list_length[i]
                i += 1

        # 绘制横线
        for t in range(self.nodenum + 3):
            idraw.line([(0, 60 * (t + 1)), (image_width, 60 * (t + 1))], fill="#e1e1e1", width=1)
        # 绘制竖线
        idraw.line([(100, 60), (100, 120)], fill="#EAEAEA", width=2)
        start_x = 100 + nodename_width
        for i in info_list_length:
            x = start_x
            end = start_x + i
            idraw.line([(x, 60), (x, image_height - 120)], fill="#EAEAEA", width=2)
            start_x = end
        # 绘制水印
        if self.watermark['enable']:
            img = self.draw_watermark(img.convert("RGBA"))
        # 保存结果
        img.save(r"./results/{}.png".format(export_time.replace(':', '-')))
        print(export_time)
        return export_time, img.size
