
<div align="center">
    <h1> FullTClash</h1>
    <p>🤖 A Telegram bot that operates based on the Clash core </p>
    <p><a href="https://github.com/AirportR/FullTclash/blob/dev/README-EN.md">English</a>&nbsp &nbsp 简体中文</p>
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


## 基本介绍

FullTClash名字来源于 Full Test base on Clash 。后端部分使用[Clash项目](https://github.com/Dreamacro/clash)(现在亦可称之为[mihomo](https://github.com/MetaCubeX/mihomo))相关代码作为出站代理，前端部分使用Telegram API作为交互界面，需配合Telegram使用，即为一个Telegram机器人(bot)， FullTClash bot 是承载其测试任务的Telegram 机器人（以下简称bot）。\
目前支持以Clash配置文件为载体的**批量**连通性测试，支持以下测试条目:
1. Netflix  
2. Youtube 
3. DisneyPlus 
4. steam货币 
5. OpenAI(ChatGPT) 
6. 落地ip风险(IP欺诈度) 
7. 维基百科
8. TVBAnyware
9. Viu

此外还有：

1. HTTP延迟测试
2. 链路拓扑测试（节点出入口分析）。
3. 下行速度测试

## 分支说明
* [master](https://github.com/AirportR/FullTclash/tree/master) 主分支，主打稳定。  
* [backend](https://github.com/AirportR/FullTclash/tree/backend) 纯后端代码，无前端BOT，意味着需要额外的bot作主端。  
* [dev](https://github.com/AirportR/FullTclash/tree/dev) 开发进度最前沿。  
* [old](https://github.com/AirportR/FullTclash/tree/dev) 依靠调用原版Clash Restful API进行测试。可随意更换内核，但已停止新功能开发。  

## 支持协议

| 出站协议           | Clash | Clash.Meta |
|----------------|-------|------------|
| SOCKS (4/4a/5) | √     | √          |
| HTTP(S)        | √     | √          |
| Shadowsocks    | √     | √          |
| VMess          | √     | √          |
| Trojan         | √     | √          | 
| Snell          | √     | √          | 
| VLESS          |       | √          |
| TUIC           |       | √          |
| Hysteria       |       | √          |
| Hysteria2      |       | √          |
| Wireguard      |       | √          |
| ShadowsocksR   | √     | √          |
----------------------
本项目默认使用Clash原生内核，需要Clash.Meta支持请参阅代理客户端编译一栏。
## 使用文档

可以在 [这里](https://fulltclash.gitbook.io/fulltclash-doc) 找到FullTclash的使用文档。
## 效果预览

流媒体测试:

![测试图片](https://upload.cc/i1/2023/03/30/xyTGRu.png)

![测试图片](https://upload.cc/i1/2023/03/30/1gdtWf.png)

## 如何开始

### 基础准备

要成功运行该Telegram 机器人，首先需要准备以下信息：

- Telegram 的api_id 、api_hash [获取地址](https://my.telegram.org/apps) 不会请Google。(部分IP已被拉黑，无法正常申请成功，请尝试更换干净IP)  

- 去 [@BotFather](https://t.me/BotFather) 那里创建一个机器人，获得该机器人的bot_token，应形如：  
  
  bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
  
  这步不会请Google。

- 字体文件。（可选，可以用默认的）  
### 拉取源码
方法1：直接下载（不会有人不知道在哪下吧？）\
方法2：使用git（Linux推荐，方便更新），首先安装git，然后拉取仓库。以下指令为 Ubuntu 发行版作示例，Windows自行解决。
```shell
apt install -y git && git clone https://github.com/AirportR/FullTclash.git && cd FullTclash
```
此方法在中国大陆可能需要代理加速，请自行解决。
### 环境准备

- Python 3.9 以上  
- 以及各种相关包依赖  

您可以用以下命令，在当前项目目录下运行以快速安装环境：

>Windows:
>```shell
>pip install -r requirements.txt
>```

>Linux:
>```shell
>pip3 install -r requirements.txt
>```
### 为bot进行相关配置
以下为启动bot的最低要求（如果您是新手，建议先以最低要求把bot跑起来，否则自己乱改配置容易出现不可预知的错误。）
- 管理员配置  
  
  新建一个名为config.yaml的文件，放在./resources下，项目有模板例子名为./resources/config.yaml.example,在config.yaml中写入如下信息： 
  
  ```yaml
  admin:
  - 12345678 # 改成自己的telegram uid
  - 8765431 # 这是第二行，表示第二个管理员，没有第二个管理员就把该行删除。
  ```
  
- bot相关配置  
  ```yaml
  bot:
   api_id: 123456 #改成自己的api_id
   api_hash: 123456ABCDefg #改成自己的api_hash
   bot_token: 123456:ABCDefgh123455  # bot_token, 从 @BotFather 获取
   # 如果是在中国大陆地区使用，则程序需要代理才能连接上Telegram服务器。写入如下信息：
   proxy: 127.0.0.1:7890 #socks5 替换成自己的代理地址和端口
  ```

- 代理客户端路径配置
 
  从3.6.5版本开始，不再默认提供代理客户端二进制文件，请自行前往以下网址获取: 
  https://github.com/AirportR/FullTCore/releases \
  下载解压后可以放到 ./bin/ 目录下，比如文件名为 FullTCore ，下面的配置文件这样写：
  ```yaml
  clash:
   path: "./bin/FullTCore" #这里改成代理客户端文件路径
  ```
  Windows系统名字后缀名.exe要加上，其他类Unix系统不需要加后缀名。
- 代理配置（可选）  
  
  如果是在中国大陆地区使用，可能部分订阅网址无法直接连接。可在config.yaml中写入如下信息： 
  
  ```
  # 获取订阅时使用代理（可选）
  proxy: 127.0.0.1:7890 #http 替换成自己的代理地址和端口,注意，此配置与上面的独立分开。
  ```
  
- 自定义buildtoken(可选)
  
  buildtoken是构建 ./bin/fulltclash(.exe) 代理客户端二进制文件的编译Token，此token为数据加密密钥，一般来说，用项目自带的编译token在本地运行不会有任何问题，但是如果以前后端模式运行，则主端需要自行编译代理后端的二进制文件，以此用到编译token，这个token需要写入到配置文件里，供主端加密信息。
  ```yaml
  buildtoken: 12345678ABCDEFG
  ```
### 获取session文件（可选）

您需要在项目文件目录下，放置一个已经登陆好的.session后缀文件，这个文件是程序生成的，是Telegram的登录凭据，形如： my_bot.session
>方法1：可以直接在配置文件config.yaml中配置，这样程序启动后会自动读取配置文件里面的值来生成session文件(要求一定要正确)。
```yaml
#配置文件示例，注意缩进要正确
bot:
 api_id: 123456
 api_hash: 123456ABCDefg
 bot_token: 123456:ABCDefgh123455
```
>方法2： 您可以参阅[这篇文档](https://docs.pyrogram.org/start/auth)，以快速获得后缀为 .session 的文件

>方法3： 项目的 ./utils/tool/ 目录下有一个文件名为 login.py ，可以通过指令运行它：
>```
>python .\login.py
>```

当程序退出后即可自动生成一个名为 my_bot.session 的文件 ，之后将它移动到项目根目录。
运行后它会尝试给你输入的用户名的目标发送消息，当接收到：嗨, 我在正常工作哦！

这句话时，即可说明该session文件有效，否则无效。

如果启动后无法验证，请删除生成的mybot.session文件，此时的文件是坏的，不可用，如果不删除程序会一直使用坏的文件，不会重新生成。
### 开始启动
配置好后，在项目目录下运行以下指令

>Windows:
>```shell
>python main.py
>```

>Ubuntu(Linux):
>```shell
>python3 main.py
>```

等待初始化操作，出现“程序已启动!”字样就说明在运行了。
运行之后和bot私聊指令：
>/testurl <订阅地址>(clash配置格式)即可开始测试

>/help 可查看所有命令说明
### 代理客户端编译(高级)
FullTclash有专用的代理客户端，存放在 ./bin/下。其中:

fulltclash-linux-amd64为 Linux-amd64 所支持\
fulltclash-windows-amd64 为 Windows-amd64 所支持的

没有所用架构？
如果没有您所用架构的二进制文件，比如arm64，或者您担心仓库自带的有安全隐患，那么您可以自行编译。

在 [此仓库](https://github.com/AirportR/FullTCore) 下有一源码文件为 fulltclash.go ，您需要将该文件自行用Golang编译器编译成二进制文件。


编译完成覆盖原文件即可 ，如果操作难度太大，可以发起issue详谈。
### Docker启动
[./docker/ 目录](https://github.com/AirportR/FullTclash/tree/dev/docker)
### 为程序设置进程守护(Linux)
由于Linux系统特性，关闭ssh连接后，前台程序会被关闭。您需要设置进程守护，才能在后台不间断地持久化运行程序。具体方法Google搜索即可。
## 交流探讨
我们欢迎各方朋友提出针对性的反馈：
- [TG更新发布频道](https://t.me/FullTClash)  
- 在项目页面提出issue

## 如何给本项目做贡献：
1、在本项目的主GitHub仓库进行fork，你可以只fork dev的分支。 \
2、在你的计算机上使用git clone来下载你fork后的仓库。 \
3、在下载后的本地仓库进行修改。\
4、执行git add .（请不要忘记句号！！！）\
5、执行git commit，并输入你做出的更改。\
6、回到你的仓库，发起pr请求到dev分支，等待下一步（通过/驳回/修改）。

## 答疑
1. FullTClash测试原理\
原理是在后台启动一个代理客户端，然后开启多个socks5入站端口，通过配置里的配置信息匹配代理客户端出站协议类型进行测试。代理客户端是基于上游的Clash项目改动得到的专属客户端，并将其命名为FullTCore。  
2. 为什么不使用原版的Clash客户端二进制\
自从FullTclash的3.5.8版本起，支持前后端模式，我们把后端部分单独分离，使之可以让前端的bot运行环境与后端运行的环境不在同一台机器上，在当时Clash并没有提供符合本项目的特性，再加上FullTClash仅仅只需要其中出站功能，所以不得已进行一些改动。事实上，FullTClash的old分支是依靠Clash提供的Restful API运行的，现在已不再维护。  
3. 什么是Telegram UID\
Telegram官方并没有承认UID的说法，但确实存在于Telegram中。每一个TG用户都存在一个唯一的身份ID，这个在官方的TG客户端是查询不到的。Bot依靠UID确定管理员身份，至于如何获取Google搜索即可。  
4. 是否有一键部署脚本\
目前只有Docker部署脚本，期待你的贡献！  

## 致谢

- [流媒体解锁思路](https://github.com/lmc999/RegionRestrictionCheck)  
- [Clash](https://github.com/Dreamacro/clash) ==> [mihomo](https://github.com/MetaCubeX/mihomo)  [GPLv3]
- [aiohttp](https://github.com/aio-libs/aiohttp)  [Apache2]  
- [pyrogram](https://github.com/pyrogram/pyrogram)  [LGPLv3]  
- [async-timeout](https://github.com/aio-libs/async-timeout)  [Apache2]    
- [Pillow](https://github.com/python-pillow/Pillow)  [HPND]  
- [pilmoji](https://github.com/jay3332/pilmoji)  [MIT]  
- [pyyaml](https://github.com/yaml/pyyaml)  [MIT]  
- [APScheduler](https://github.com/agronholm/apscheduler)  [MIT]  
- [loguru](https://github.com/Delgan/loguru)  [MIT]  
- [geoip2](https://github.com/maxmind/GeoIP2-python)  [Apache2]  
- [cryptography](https://github.com/pyca/cryptography)  [Apache2] [BSD3]  
- [google-re2](https://github.com/google/re2)  [BSD3]
- [aiohttp_socks](https://github.com/romis2012/aiohttp-socks)  [Apache2]