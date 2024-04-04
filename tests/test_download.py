import asyncio
import sys
import unittest
from os import getcwd, chdir


def pin_cwd():
    """
    固定工作目录为项目根目录
    """
    if "tests" in getcwd():
        chdir("..")
    sys.path.append(getcwd())
    print(f"当前工作目录： {getcwd()}")
    # print(f"包的搜索路径：{sys.path}")


class TestDownload(unittest.TestCase):
    def setUp(self):
        pin_cwd()
        from utils.collector import Download
        durl = "https://github.com/AirportR/FullTCore/releases/download/v1.3-meta/FullTCore_1.3-meta_windows_amd64.zip"
        dl = Download(durl, "./tests", durl.split("/")[-1])
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.dl = dl
        self.loop = loop

    def test_init(self):
        self.assertTrue(self.loop.run_until_complete(self.dl.dowload()))


if __name__ == '__main__':
    unittest.main()
