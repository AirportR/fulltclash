import sys
from os import getcwd, chdir
import unittest


def pin_cwd():
    """
    固定工作目录为项目根目录
    """
    if "tests" in getcwd():
        chdir("..")
    sys.path.append(getcwd())
    print(f"当前工作目录： {getcwd()}")
    # print(f"包的搜索路径：{sys.path}")


class TestInit(unittest.TestCase):
    def setUp(self):
        pin_cwd()
        from utils.init import check_init
        self.func = check_init

    def test_init(self):
        self.assertTrue(self.func())


if __name__ == '__main__':
    # pin_cwd()

    unittest.main()
    # check_init()
    print("✅测试通过")
