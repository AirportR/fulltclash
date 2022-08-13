from pyrogram.errors import RPCError
from loguru import logger


async def check_number(message, test_member, max_num=4):
    """
    检查任务数量
    :param message: 消息对象
    :param test_member: 当前任务数量
    :param max_num: 最大测试数量
    :return: bool
    """
    try:
        if test_member > max_num:
            await message.edit_text("⚠️测试任务数量达到最大，请等待一个任务完成。")
            return True
        if test_member > 1:
            logger.warning("注意，当前测试任务数量大于1，处于多任务同测状态，可能会对测试结果产生影响")
            await message.reply("⚠️注意，当前测试任务数量大于1，处于多任务同测状态，可能会对测试结果产生影响")
        return False
    except RPCError as r:
        logger.error(r)


async def check_url(message, url):
    """
    检查url
    :param message:
    :param url:
    :return: bool
    """
    if not url:
        try:
            await message.edit_text("⚠️无效的订阅地址，请检查后重试。")
        except RPCError as r:
            logger.error(r)
        return True
    return False


async def check_sub(message, subconfig):
    """
    检查订阅是否获取成功
    :param message:
    :param subconfig:
    :return: bool
    """
    if not subconfig:
        logger.warning("ERROR: 无法获取到订阅文件")
        try:
            await message.edit_message_text("ERROR: 无法获取到订阅文件")
        except RPCError as r:
            logger.error(r)
        return True
    else:
        return False


async def check_nodes(message, nodenum, args: tuple, max_num=500):
    """
    检查获得的关键信息是否为空，以及节点数量是否大于一定数值
    :param max_num: 最大节点数量
    :param message: 消息对象
    :param nodenum: 节点数量
    :param args: 若干信息
    :return: bool
    """
    if nodenum is None:
        try:
            message.edit_message_text("❌发生错误，请检查订阅文件")
        except RPCError as r:
            logger.error(r)
    for arg in args:
        if arg is None:
            try:
                message.edit_message_text("❌发生错误，请检查订阅文件")
            except RPCError as r:
                logger.error(r)
            return True
        else:
            pass
    if nodenum > max_num:
        logger.warning("❌节点数量过多！已取消本次测试")
        try:
            await message.edit_text("❌节点数量过多！已取消本次测试")
        except RPCError as r:
            logger.error(r)
        return True
    else:
        return False


async def check_photo(message, back_message, name, nodenum, wtime):
    """
    检查图片是否生成成功
    :param wtime: 消耗时间
    :param nodenum: 节点数量
    :param message: 消息对象
    :param back_message: 消息对象
    :param name: 图片名
    :return:
    """
    try:
        if name is None:
            await back_message.edit_text("⚠️生成图片失败,可能原因:节点名称包含国旗⚠️\n")
        else:
            if nodenum > 50:
                await message.reply_document(r"./results/{}.png".format(name),
                                             caption="⏱️总共耗时: {}s".format(wtime))
            else:
                await message.reply_photo(r"./results/{}.png".format(name),
                                          caption="⏱️总共耗时: {}s".format(wtime))
            await back_message.delete()
            await message.delete()
    except RPCError as r:
        logger.error(r)


def check_rtt(rtt, nodenum: int):
    if rtt == 0:
        new_rtt = [0 for _ in range(nodenum)]
        return new_rtt
    else:
        return rtt
