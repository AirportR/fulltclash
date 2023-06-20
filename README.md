
<div align="center">
    <h1> FullTClash</h1>
    <p>🤖 A Telegram bot that operates based on the Clash core </p>
    <p><a href="https://github.com/AirportR/FullTclash/blob/dev/README-EN.md">English</a>   简体中文</p>
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

## 最近更新(3.5.9)
✏️3.5.9版本更新日志：

🧵 改进测试方法。移除动态连接库调用的形式，更稳定的体验。\
⚠️注意，如果您是在3.5.4版本后开始使用本项目，请把以下配置删除或修改(linux):
```yaml
clash:
 path: ./bin/fulltclash-linux-amd64
```


同时动态链接库此版本已经移除，继续在方向上开发是不明智的选择。\
🐛 修复3.5.8版本偶现拓扑图绘制失败的bug。\
📖 新增回调功能的详细文档：https://fulltclash.gitbook.io/fulltclash-doc/hui-tiao-gong-neng-gao-ji \
✨ 支持设置默认的后端名称展示。前往配置样例查看（文档那边暂时未更新）。\
✨ Youtube解锁检测现已支持 送中(CN) 结果展示。\
⬆️新增包依赖。请使用 pip install lxml==4.9.2 进行安装。





历史更新请到TG频道查看: 

https://t.me/FullTClash

## 基本介绍

FullTclash bot 是承载其测试任务的Telegram 机器人（以下简称bot）,目前支持以clash配置文件为载体的**批量**联通性测试,支持以下测试条目:
>- Netflix  Youtube DisneyPlus Bilibili steam货币 OpenAI(ChatGPT) 落地ip风险(IP欺诈度) 维基百科  

以及HTTP延迟测试和链路拓扑测试（节点出入口分析）。  
## 使用文档

可以在 [这里](https://fulltclash.gitbook.io/fulltclash-doc) 找到FullTclash的使用文档。
## 效果预览

流媒体测试:

![测试图片](https://upload.cc/i1/2023/03/30/xyTGRu.png)

![测试图片](https://upload.cc/i1/2023/03/30/1gdtWf.png)

## 如何开始

### 基础准备

要成功运行该项目代码，首先需要准备以下信息：

- Telegram 的api_id 、api_hash [获取地址](https://my.telegram.org/apps) 不会请Google。(部分TG账号已被拉黑，无法正常使用)  

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

您需要在项目文件目录下，放置一个已经登陆好的.session后缀文件，这个文件是程序生成的，形如： my_bot.session
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
>/clash start 用于启动clash，否则测试结果会全部是N/A。

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
教程文档待更新
### 为程序设置进程守护(Linux)
由于Linux系统特性，关闭ssh连接后，前台程序会被关闭。您需要设置进程守护，才能在后台不间断地运行程序。具体方法Google搜索即可。
## 交流探讨
我们欢迎各方朋友提出针对性的反馈：
- [TG更新发布频道](https://t.me/FullTClash)  
- 在项目页面提出issue  
## 致谢

- [流媒体解锁思路](https://github.com/lmc999/RegionRestrictionCheck)  
- [Clash](https://github.com/Dreamacro/clash)  
- [aiohttp](https://github.com/aio-libs/aiohttp)  
- [pyrogram](https://github.com/pyrogram/pyrogram)  
- [async-timeout](https://github.com/aio-libs/async-timeout)  
- [Pillow](https://github.com/python-pillow/Pillow)  
- [pilmoji](https://github.com/jay3332/pilmoji)  
- [pyyaml](https://github.com/yaml/pyyaml)  
- [requests](https://github.com/psf/requests)  

## 如何给本项目做贡献：
1、在本项目的主GitHub仓库进行fork，你可以只fork dev的分支。 \
2、在你的计算机上使用git clone来下载你fork后的仓库。 \
3、在下载后的本地仓库进行修改。\
4、执行git add .（请不要忘记句号！！！）\ 
5、执行git commit，并输入你做出的更改。\
6、回到你的仓库，发起pr请求，等待下一步（通过/驳回/修改）。

如果不这样做可能会：

1、仓库维护者看到的是一片绿色加号，根本不知道你改了什么。\
2、你的操作会很麻烦，可能还会改错文件。\
3、维护者很难看懂你都干了些什么。