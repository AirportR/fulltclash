
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

## 一键启动
**前提**: 类Unix系统需要安装git，python3（python3.9以上），pip3。Windows系统安装python并添加环境变量，以及git。
* powershell
```powershell
git clone -b backend https://github.com/AirportR/FullTclash.git; cd FullTclash;pip install -r requirements.txt; $randomString = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 10 | ForEach-Object { [char]$_ });python main.py -t ${randomString} -b 0.0.0.0:8765 --path ${randomString}
```

* bash等
```bash
git clone -b backend https://github.com/AirportR/FullTclash.git && cd FullTclash && pip3 install -r requirements.txt && randomString=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1) && python3 main.py -t $randomString -b 0.0.0.0:8765 --path $randomString
```

### Docker启动
> Docker镜像是基于alpine构建的

```bash
docker run -idt \
   --name fulltclash-ws \
   -e branch=origin \
   -e core=4 \
   -e token=114514 \
   -e buildtoken=BUILDTOKEN \
   -p 8765:8765 \
   --restart always \
   airportr/fulltclash:ws
```
