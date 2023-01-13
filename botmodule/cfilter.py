from pyrogram import filters


def dynamic_data_filter(data):
    async def func(flt, _, query):
        return flt.data == query.data

    # "data" kwarg is accessed with "flt.data" above
    return filters.create(func, data=data)


def my_filter(queue):
    async def func(flt, _, message):
        return flt.queue.empty()

    return filters.create(func, queue=queue)
