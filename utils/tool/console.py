import asyncio
import sys
from os import getcwd, chdir
from pathlib import Path


def change_cwd():
    if "utils" in getcwd():
        chdir("..")
        change_cwd()
    else:
        sys.path.append(getcwd())
        return


change_cwd()

if __name__ == "__main__":
    import argparse
    from utils import cleaner
    from utils.backend import check_init, SpeedCore, ScriptCore, TopoCore

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    check_init()

    config_path = ''
    core = None


    def get_proxies(path: str):
        url = cleaner.geturl(path)
        if url:
            from utils.collector import SubCollector
            subcontent = loop.run_until_complete(SubCollector(url).getSubConfig(inmemory=True))
            pre_cl = cleaner.ClashCleaner(':memory:', subcontent)
            pre_cl.node_filter(include_text, exclude_text)
            return pre_cl.getProxies()
        else:
            with open(path, 'r', encoding='utf-8') as fp:
                data = cleaner.ClashCleaner(fp)
                data.node_filter(include_text, exclude_text)
            return data.getProxies()


    def export_to_image():
        file_name = ""
        if args.temp and _test_type != "script":
            print("测试结果:", resd)
            return
        from utils.export import ExportCommon, ExportSpeed, ExportTopo
        if _test_type == "speed":
            file_name = ExportSpeed(name=None, info=resd).exportImage()
        elif _test_type == "topo":
            info1 = resd.get('inbound', {})
            info1['task'] = resd.get('task', {})
            info2 = resd.get('outbound', {})
            info2['task'] = resd.get('task', {})
            clone_info2 = {}
            clone_info2.update(info2)
            ex1 = ExportTopo()
            _, __, image_width2 = ex1.exportTopoOutbound(None, clone_info2)
            ex2 = ExportTopo(name=None, info=info1)
            file_name, _ = ex2.exportTopoInbound(info2.get('节点名称', []), info2, image_width2)
        elif _test_type == "script":
            temp = True if args.temp else False
            file_name = ExportCommon(resd.pop("节点名称", []), resd).draw(debug=temp)
        if file_name:
            if args.temp and _test_type == "script":
                print("测试结果:", resd)
            else:
                print("测试结果图片已保存在: ", str(Path(getcwd()).joinpath(f"results/{file_name}")))


    parser = argparse.ArgumentParser(description="FullTClash命令行简易测试，不用启动bot。")
    parser.add_argument("-f", "--file", required=True, type=str, help="订阅文件路径")
    parser.add_argument("-c", "--core", required=True, type=str, help="订阅文件路径，支持本地路径和URL路径")
    parser.add_argument("-i", "--include", required=False, type=str, help="包含过滤器")
    parser.add_argument("-e", "--exclude", required=False, type=str, help="排除过滤器")
    parser.add_argument("--temp", action='store_true', help="临时输出测试结果，将自动打开测试结果图片(仅对script类型有效)，"
                                                            "图片不保存到本地。")

    args = parser.parse_args()
    if args.core == 'speed':
        core = SpeedCore()
        _test_type = str(args.core)
    elif args.core == 'script':
        core = ScriptCore()
        _test_type = str(args.core)
    elif args.core == 'topo':
        core = TopoCore()
        _test_type = str(args.core)
    else:
        raise TypeError("Unknown test type, please input again.\n未知的测试类型，请重新输入!")
    include_text = ""
    exclude_text = ""
    file_path = ""
    if args.include:
        include_text = args.include
    if args.exclude:
        exclude_text = args.exclude
    if args.file:
        file_path = args.file

    try:
        if core is None:
            print("未找到核心")
            sys.exit()
        my_proxies = get_proxies(file_path)
        resd: dict = loop.run_until_complete(core.core(my_proxies))
    except Exception as e:
        print(e)
        sys.exit()
    try:
        export_to_image()
    except Exception as _e:
        print(_e)
        print("测试结果绘图失败！以下是原始测试结果: \n", resd)
