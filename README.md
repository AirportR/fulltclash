
<div align="center">
    <h1> FullTClash</h1>
    <p>🤖 A Telegram bot that operates based on the Clash core </p>
    <a href="https://fulltclash.gitbook.io/fulltclash-doc"><img src="https://img.shields.io/static/v1?message=doc&color=blue&logo=micropython&label=FullTClash"></a> 
    <img src="https://img.shields.io/github/license/AirportR/FullTclash">
    <a href="https://app.codacy.com/gh/AirportR/FullTclash/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade"><img src="https://app.codacy.com/project/badge/Grade/389b2787eb7647dfad486ccaa70eabf4"></a>
    <a href="https://github.com/AirportR/FullTclash/issues"><img src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat"></a>
    <br>
    <a href="https://github.com/AirportR/FullTclash/"><img src="https://img.shields.io/github/stars/AirportR/FullTclash?style=social"></a>
	<a href = "https://t.me/FullTclash"><img src="https://img.shields.io/static/v1?style=social&logo=telegram&label=channel&message=channel" ></a>
	<br>
	<br>
</div>


## 分支

**注意!**  

当前为backend分支，纯后端代码，无任何前端(bot)部分，需要前端部分请前往其他分支.

## 使用

请先进行安装 [requirements.txt](https://raw.githubusercontent.com/AirportR/FullTclash/backend/requirements.txt) 里的第三方库:

```shell
pip3 install -r requirements.txt
```
```text
usage: python3 main.py [-h] [-b BIND] -t TOKEN [-f BUILDTOKEN]

FullTClash-纯后端命令行快速启动

options:
  -h, --help            show this help message and exit
  -b BIND, --bind BIND  覆写绑定的外部地址端口，默认为0.0.0.0:8765
  -t TOKEN, --token TOKEN
                        Websocket通信Token，也叫做密码，防止不合法的请求。
  -f BUILDTOKEN, --buildtoken BUILDTOKEN
                        FullTCore代理客户端的buildtoken，不填则为默认值

```

## 启动示例:

```shell
python3 main.py -t fulltclash -b 0.0.0.0:8765
```