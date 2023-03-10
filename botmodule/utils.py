import asyncio

message_delete_queue = asyncio.Queue()  # put the value as a tuple: (chat.id, msg.id, seconds)
