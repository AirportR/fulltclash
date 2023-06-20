# from pyrogram.types import Message
# from pyrogram import Client
# from utils import message_delete_queue

# 这是一个写权限回调的模板
# 首先需要定义一个名为 callback 的协程函数（一定要这个名字），然后下面是一个例子，不管你怎么操作，最后一定要返回一个布尔值。
# 若为True，则通过权限校验。否则拒绝调用bot的指令。


# async def callback(app: Client, message: Message) -> bool:
#     """
#     app 参数为 Bot的客户端主程序
#     message 参数为 触发回调的消息对象
#
#     返回值一定为布尔值
#     """
#     try:
#         await message.reply("回调函数调用成功！")
#         return False
#     except Exception as e:
#         print(e)
#         return True
