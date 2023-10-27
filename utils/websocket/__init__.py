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


wsqueue = WebSocketQueue(100)
