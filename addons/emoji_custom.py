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
"""


class EmojiPediaSource(pilmoji.source.DiscordEmojiSourceMixin):
    """A base source that fetches emojis from emojipedia."""

    BASE_EMOJIPEDIA_URL: ClassVar[
        str
    ] = "https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/"
    STYLE: ClassVar[Optional[str]] = None

    def get_emoji(self, emoji: str, /) -> Optional[BytesIO]:  # type: ignore
        if self.STYLE is None:
            raise TypeError("STYLE class variable unfilled.")

        name = demojize(emoji).strip(":️").replace("_", "-")
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