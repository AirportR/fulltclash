from botmodule.command.grant import *
from botmodule.command.submanage import *
from botmodule.command.test import *
from botmodule.command.authority import *
from botmodule.command.basic import *
from botmodule.command.setting import *
from botmodule.command.download import *
from botmodule.command.connect import *
from botmodule.command.reboot import *
from botmodule.command import common_command
from botmodule.command.edit import *
from botmodule import register
from botmodule import subinfo
from botmodule.record import init_memory_ranking


init_memory_ranking()
__all__ = ['grant', 'ungrant', 'user', 'restart_or_killme',
           'sub_invite', 'sub', 'new', 'remove',
           'process', 'invite', 'invite_pass',
           'version', 'helps',
           'test_setting', 'select_page', 'get_sort_str', 'select_sort', 'home_setting',
           'download_script', 'reload_addon_from_telegram', 'uninstall_script',
           'common_command', 'select_export', 'SPEEDTESTIKM', 'BOT_MESSAGE_LIST', 'task_handler',
           'select_slave_only_1']
