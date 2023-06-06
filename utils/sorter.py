from loguru import logger
from utils import cleaner


# """
# 这个模块是一些排序的实现
# """


def sort_nodename_topo(_cleaner: cleaner.ClashCleaner):
    """
    排序节点，将一个配置文件里面的节点进行排序，排序规则是相同入口的节点都是相邻的，方便节点分析。这个排序函数专为节点分析设计的。
    :param _cleaner: 一个clash配置清洗器
    :return: list,dict,cleaner.ClashCleaner 返回排序好的节点名,以及入口ip对应的出口数量。此外第三个返回值返回修改过的clashcleaner
    """
    try:
        cl = _cleaner
        proxylist = cl.getProxies()
        ipstack = [p['server'] for p in proxylist]
        ipcu = [p['server'] for p in proxylist]
        for i, p in enumerate(proxylist):
            p['ipstart'] = ipstack[i]
        for i, p in enumerate(proxylist):
            p['ipcu'] = ipcu[i]
        ipstack_list = cleaner.batch_ipstack(proxylist)
        ipcu_list = cleaner.batch_ipcu(ipstack_list)
        ipaddrs = cleaner.batch_domain2ip(ipcu_list)
        addrs2 = sorted(ipaddrs, key=lambda i1: i1['server'])
        list1 = []
        dict1 = {}
        dict2 = {}
        for n in addrs2:
            list1.append(n['server'])
            dict1.setdefault(n['server'], n['ipstart'])
            dict2.setdefault(n['server'], n['ipcu'])
        cl.yaml['proxies'] = addrs2
        nodename = cl.nodesName()
        info = cleaner.ClashCleaner.count_elem(list1)
        ipsdata = dict1
        iptcu = dict2
        return nodename, info, cl, ipsdata, iptcu
    except Exception as e:
        logger.error(str(e))
        return None, None, None, None, None

# def ping(_ping: list, proxyname: list):
#     """
#     用ping值排序，值从低到高。
#     排序思路：先将超时的节点单独分离到新字典，原来的字典剔除超时节点，开始依靠延迟数字进行排序。然后从排好的结果中拿数据。最后加上超时的数据。
#     那两个变量进行存放，var1存放排好节点名，var2存放排好的延迟。两者是对应的。
#     :return: 排序好的 [节点名] [延迟]
#     """
#     delays = {}
#     timeout_item = {}
#     for t in range(len(proxyname)):
#         delays[proxyname[t]] = _ping[t]
#
#     for k, v in delays.items():
#         if v == -1:
#             timeout_item[k] = v
#     for k0 in timeout_item.keys():
#         delays.pop(k0)
#     res1 = sorted(delays.items(), key=lambda kv: [kv[1], kv[0]])
#     print(res1)
#     var1 = []
#     var2 = []
#     for i in res1:
#         var1.append(i[0])
#         var2.append(i[1])
#     for k1, v1 in timeout_item.items():
#         var1.append(k1)
#         var2.append(v1)
#     return var1, var2
