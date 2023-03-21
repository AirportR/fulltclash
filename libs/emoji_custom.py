import abc
import contextlib
import re
import os
import shutil
from io import BytesIO
from typing import ClassVar, Optional
from aiohttp import ClientSession
import pilmoji
import requests
from emoji import demojize

"""
自定义的emoji表情源
保留原作者信息
author: https://github.com/Oreomeow
修改: 增加本地源
"""


class EmojiPediaSource(pilmoji.source.DiscordEmojiSourceMixin):
    """A base source that fetches emojis from emojipedia."""

    BASE_EMOJIPEDIA_URL: ClassVar[str] = "https://em-content.zobj.net/thumbs/120/"
    STYLE: ClassVar[Optional[str]] = None

    def get_emoji(self, emoji: str, /) -> Optional[BytesIO]:  # type: ignore
        if self.STYLE is None:
            raise TypeError("STYLE class variable unfilled.")

        name = demojize(emoji).strip(":️").replace("_", "-").replace("-&-", "-").replace(".", "")
        if name[0].isupper():
            name = f"flag-{name.lower()}"
        uni = re.sub(
            r"\\u0*",
            "-",
            emoji.encode("unicode_escape").decode("utf-8"),
            flags=re.IGNORECASE,
        ).lstrip("-")
        url = self.BASE_EMOJIPEDIA_URL + self.STYLE + name + "_" + uni + ".png"

        with contextlib.suppress(requests.HTTPError):
            return BytesIO(self.request(url))


class ApplePediaSource(EmojiPediaSource):
    """A source that uses Apple emojis."""

    STYLE = "apple/325/"


class GooglePediaSource(EmojiPediaSource):
    """A source that uses Google Noto Color Emoji emojis."""

    STYLE = "google/346/"


class SamsungPediaSource(EmojiPediaSource):
    """A source that uses Samsung emojis."""

    STYLE = "samsung/320/"


class MicrosoftPediaSource(EmojiPediaSource):
    """A source that uses Microsoft emojis."""

    STYLE = "microsoft/319/"


class WhatsAppPediaSource(EmojiPediaSource):
    """A source that uses WhatsApp emojis."""

    STYLE = "whatsapp/326/"


class TwitterPediaSource(EmojiPediaSource):
    """A source that uses Twitter emojis."""

    STYLE = "twitter/322/"


class FacebookPediaSource(EmojiPediaSource):
    """A source that uses Facebook emojis."""

    STYLE = "facebook/327/"


class MicrosoftTeamsPediaSource(EmojiPediaSource):
    """A source that uses Microsoft Teams emojis."""

    STYLE = "microsoft-teams/337/"


class SkypePediaSource(EmojiPediaSource):
    """A source that uses Skype emojis."""

    STYLE = "skype/289/"


class JoyPixelsPediaSource(EmojiPediaSource):
    """A source that uses JoyPixels emojis."""

    STYLE = "joypixels/340/"


class TossFacePediaSource(EmojiPediaSource):
    """A source that uses TossFace emojis."""

    STYLE = "toss-face/342/"


class LocalSource(pilmoji.source.BaseSource):
    def get_emoji(self, emoji: str, /) -> Optional[BytesIO]:
        file_path = self.get_file_path(emoji)
        try:
            with open(file_path, "rb") as file:
                return BytesIO(file.read())
        except FileNotFoundError:
            pass
        return None

    def get_discord_emoji(self, _id: int, /) -> Optional[BytesIO]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_file_path(self, emoji: str) -> str:
        return ''

    @abc.abstractmethod
    def download_emoji(self, download_url):
        pass


class TwemojiLocalSource(LocalSource):
    """
    图片源：https://github.com/twitter/twemoji/tree/master/assets/72x72
    安装路径：./resources/emoji/twemoji
    """

    def __init__(self, init: str = None, proxy=None):
        """
        构造函数中，如果init不为none，则提供下载emoji资源包的url地址
        """
        self.savepath = './resources/emoji/twemoji.zip'
        self._download_url = 'https://github.com/twitter/twemoji/archive/refs/tags/v14.0.2.zip'
        if init is None:
            return
        self.download_emoji(init, proxy=proxy)
        self.init_emoji(self.savepath)

    @property
    def download_url(self):
        return self._download_url

    @staticmethod
    def init_emoji(savepath: str):
        # 解压下载好的文件
        shutil.unpack_archive(savepath, './resources/emoji/', format='zip')
        # print("解压完成")
        # 重命名
        dirs = os.listdir('./resources/emoji/')
        for d in dirs:
            if d.startswith('twemoji') and not d.endswith('.zip'):
                os.rename(os.path.join(os.path.abspath('./resources/emoji/'), d),
                          os.path.join(os.path.abspath('./resources/emoji/'), 'twemoji'))
                break
        return os.path.isdir('./resources/emoji/twemoji')

    async def download_emoji(self, download_url: str = None, savepath='./resources/emoji/twemoji.zip', proxy=None):
        # 如果本地已存在，便无需重新下载
        if os.path.isdir('./resources/emoji/twemoji'):
            return

        _url = self.download_url if download_url is None else download_url  # 如果没有提供下载地址则用默认的
        print("Download URL:", _url)
        # 从网络上下载
        async with ClientSession(headers={'user-agent': 'FullTclash'}) as session:
            async with session.get(_url, proxy=proxy, timeout=20) as resp:
                if resp.status == 200:
                    with open(savepath, 'wb') as f:
                        while True:
                            block = await resp.content.read(1024)
                            if not block:
                                break
                            f.write(block)
                else:
                    raise Exception(f"NetworkError: {resp.status}==>\t{_url}")

    def get_discord_emoji(self, _id: int, /) -> Optional[BytesIO]:
        pass

    def get_file_path(self, emoji: str) -> str:
        code_points = [f'{ord(c):x}' for c in emoji]
        file_path = f"./resources/emoji/twemoji/assets/72x72/{'-'.join(code_points)}.png"
        return file_path


class OpenmojiLocalSource(LocalSource):
    """
    图片源：https://github.com/hfg-gmuend/openmoji/tree/master/color/72x72
    安装路径：./resources/emoji/openmoji
    """

    def get_discord_emoji(self, _id: int, /) -> Optional[BytesIO]:
        pass

    def get_file_path(self, emoji: str) -> str:
        code_points = [f'{ord(c):04X}' for c in emoji]
        return f"./resources/emoji/openmoji/{'-'.join(code_points)}.png"

    def download_emoji(self, download_url):
        pass


__all__ = [
    "ApplePediaSource",
    "GooglePediaSource",
    "SamsungPediaSource",
    "MicrosoftPediaSource",
    "WhatsAppPediaSource",
    "TwitterPediaSource",
    "FacebookPediaSource",
    "MicrosoftTeamsPediaSource",
    "SkypePediaSource",
    "JoyPixelsPediaSource",
    "TossFacePediaSource",
    "TwemojiLocalSource",
    "OpenmojiLocalSource",
]

if __name__ == "__main__":
    from PIL import Image, ImageFont

    my_string = """
    Hello, world! 👋 Here are some emojis: 🎨 🌊 😎
    """

    with Image.new("RGB", (550, 80), (255, 255, 255)) as image:
        font = ImageFont.truetype("arial.ttf", 24)

        with pilmoji.Pilmoji(image, source=TwitterPediaSource) as pilmoji:
            pilmoji.text((10, 10), my_string.strip(), (0, 0, 0), font)

        image.show()
