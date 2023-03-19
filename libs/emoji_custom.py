import abc
import contextlib
import re
from io import BytesIO
from typing import ClassVar, Optional

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
    
    def get_discord_emoji(self, id: int, /) -> Optional[BytesIO]:
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_file_path(self,emoji: str)-> str:
        return None

class TwemojiLocalSource(LocalSource):
    '''
    图片源：https://github.com/twitter/twemoji/tree/master/assets/72x72
    安装路径：./resources/emoji/twemoji
    '''
    def get_file_path(self,emoji: str)-> str:
        code_points = [f'{ord(c):x}' for c in emoji]
        return f"./resources/emoji/twemoji/{'-'.join(code_points)}.png"

class OpenmojiLocalSource(LocalSource):
    '''
    图片源：https://github.com/hfg-gmuend/openmoji/tree/master/color/72x72
    安装路径：./resources/emoji/openmoji
    '''
    def get_file_path(self,emoji: str)-> str:
        code_points = [f'{ord(c):04X}' for c in emoji]
        return f"./resources/emoji/openmoji/{'-'.join(code_points)}.png"

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