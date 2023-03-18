from pyrogram import filters
from libs import check


# custom filter

def dynamic_data_filter(data):
    async def func(flt, _, query):
        return flt.data == query.data

    # "data" kwarg is accessed with "flt.data" above
    return filters.create(func, data=data)


def user_filter(user: list):
    async def func(flt, _, message):
        return await check.check_user(message, flt.user)

    return filters.create(func, user=user)
