import hashlib
import json
from asyncio import Queue
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Union


class PayloadStatus(Enum):
    OK = 1  # 正常
    ERROR = -1  # 异常
    NOCONTENT = 0  # 无操作


@dataclass
class WebSocketJson:
    status: PayloadStatus = PayloadStatus.NOCONTENT  # 枚举类型
    message: str = ''
    payload: Union[str, dict, list, tuple] = ''
    jsondecoder: Callable = json.dumps

    def __str__(self):
        return self.jsondecoder({
            'status': self.status.value,
            'message': self.message,
            'payload': self.payload
        })


class WebSocketQueue(Queue):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def put(self, payload: dict) -> None:
        """
        推送任务
        """
        await super().put(payload)

    async def get(self) -> dict:
        return await super().get()

    def get_nowait(self) -> dict:
        return super().get_nowait()


def parse_wspath(path: str) -> str:
    if path == '/':
        print("以根路径作为websocket连接入口是不推荐的，建议启动时设置 -path 参数")
        return path
    if path.startswith('/'):
        path = path[1:]
    path = hashlib.md5(path.encode()).hexdigest()
    path = '/' + path
    return path
