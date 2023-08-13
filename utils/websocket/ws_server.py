import asyncio
import json
import os
import sys

from aiohttp import web
from loguru import logger

from utils import websocket
from utils.backend import select_core, GCONFIG
from utils.safe import cipher_chacha20, sha256_32bytes, plain_chahcha20


async def ws_progress(progress, nodenum, ws: web.WebSocketResponse, corenum: int, payload: dict):
    progresstext = f"${corenum}:{progress}:{nodenum}"
    slave = payload.get('slave', {})
    slavecomment = slave.get('comment', None)
    edit_msg = payload.get('edit-message', {})
    edit_msg_id = edit_msg.get('message-id', None)
    edit_chat_id = edit_msg.get('chat-id', None)
    if slavecomment and edit_msg_id and edit_chat_id:
        new_payload = {'text': progresstext,
                       'comment': payload.get('slave', {}).get('comment', None),
                       'edit-message': payload.get('edit-message', {}),
                       'origin-message': payload.get('origin-message', {})}

        wjson = websocket.WebSocketJson(websocket.PayloadStatus.OK, 'edit', new_payload)
        await ws.send_str(str(wjson))


async def router(plaindata: dict, ws: web.WebSocketResponse, **kwargs):
    do = plaindata.pop('do', '')
    if do == 'run':
        key = sha256_32bytes("12345678")
        coreindex = plaindata.get('coreindex', None)
        proxyinfo = plaindata.pop('proxies', [])
        core = select_core(coreindex, (ws_progress, (ws, coreindex, plaindata)))
        if core is None:
            return
        kwargs.update(plaindata)
        logger.info("开始测试")
        info = await core.core(proxyinfo, **kwargs) if proxyinfo else {}
        plaindata['result'] = info
        print("测试结果: ", info)
        infostr = json.dumps(plaindata)
        cipherdata = cipher_chacha20(infostr.encode(), key)
        await ws.send_bytes(cipherdata)
    await ws.close()


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    KEY = GCONFIG.config.get('websocket', {}).get('token', '')
    logger.debug(f'当前数据加密密钥: {KEY}')
    if not KEY and not isinstance(KEY, str):
        logger.error("websocket通信token值读取错误，程序退出")
        sys.exit()
    async for msg in ws:
        try:
            plaindata = plain_chahcha20(msg.data, sha256_32bytes(KEY))
        except Exception as e:
            logger.warning(str(e))
            wjson = websocket.WebSocketJson(websocket.PayloadStatus.ERROR, 'Data decryption failed.', '')
            await ws.send_str(str(wjson))
            # await ws.send_str('Data decryption failed.')
            logger.warning("Data decryption failed.")
            return
        try:
            plaindata = json.loads(plaindata)
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.error("Data decryption failed.")
            wjson = websocket.WebSocketJson(websocket.PayloadStatus.ERROR, 'Data decryption failed.', '')
            await ws.send_str(str(wjson))
            # await ws.send_json({'status': 'Data decryption failed.'})
            # await ws.send_str('Data decryption failed.')
            return

        await ws.send_json(str(websocket.WebSocketJson(websocket.PayloadStatus.OK, '接受数据成功', '')))
        passwd = plaindata.get('token', '')
        if passwd != 'fulltclashdev':
            await ws.send_json(str(websocket.WebSocketJson(websocket.PayloadStatus.ERROR, '身份验证失败！', '')))
            return
        try:
            await router(plaindata, ws)
        except Exception as e:
            logger.error(str(e))
        finally:
            await ws.close()

    logger.info('Websocket connection closed')

    return ws


async def server(host: str = '0.0.0.0', port: int = 8765):
    app = web.Application()
    app.add_routes([web.get('/', websocket_handler)])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port, ssl_context=None)
    await site.start()

    logger.info(f'WebSocket server started. Listening at {host}:{port}')

    await asyncio.Future()  # run forever


def check_args():
    import argparse
    parser = argparse.ArgumentParser(description="FullTClash-纯后端命令行快速启动")
    parser.add_argument("-b", "--bind", required=False, type=str, help="覆写绑定的外部地址端口，默认为0.0.0.0:8765")
    parser.add_argument("-t", "--token", required=True, type=str, help="Websocket通信Token，也叫做密码，防止不合法的请求。")
    parser.add_argument("-f", "--buildtoken", required=False, type=str, help="FullTCore代理客户端的buildtoken，不填则为默认值")

    args = parser.parse_args()

    if args.bind:
        bindaddr = str(args.bind)
        wsconf = GCONFIG.config.get('websocket', {})
        wsconf['bindAddress'] = bindaddr
        GCONFIG.yaml['websocket'] = wsconf
        GCONFIG.reload()
        logger.info(f"已覆写监听地址：{bindaddr}")
    if args.token:
        wstoken = str(args.token)
        wsconf = GCONFIG.config.get('websocket', {})
        wsconf['token'] = wstoken
        GCONFIG.yaml['websocket'] = wsconf
        GCONFIG.reload()
        logger.info(f"已覆写Websocket通信Token")
    if args.buildtoken:
        buildtoken = str(args.buildtoken)
        GCONFIG.yaml['buildtoken'] = buildtoken
        GCONFIG.reload()
        logger.info(f"已覆写FullTCore编译Token")


async def main():
    check_init()
    check_args()
    wsconf = GCONFIG.config.get('websocket', {})
    bindaddr = wsconf.get('bindAddress', '0.0.0.0:8765')
    if not isinstance(bindaddr, str):
        logger.error("绑定地址解析错误，请重试!")
        sys.exit()
    ba = bindaddr.lstrip('http:').strip('/').split(':')
    try:
        if len(ba) != 2:
            logger.error("绑定地址解析错误，请重试!")
            sys.exit()
        port = int(ba[1])
        host = ba[0]
    except Exception as e:
        logger.error(str(e))
        host = '0.0.0.0'
        port = 8765
    task = asyncio.create_task(server(host, port))
    await task


def check_init():
    dirs = os.listdir()
    if "logs" in dirs and "results" in dirs:
        return
    logger.info("检测到初次使用，正在初始化...")
    if not os.path.isdir('logs'):
        os.mkdir("logs")
        logger.info("创建文件夹: logs 用于保存日志")
    if not os.path.isdir('results'):
        os.mkdir("results")
        logger.info("创建文件夹: results 用于保存测试结果")


if __name__ == '__main__':
    os.chdir('../..')
    asyncio.run(main())
