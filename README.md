# FullTclash

基于clash 核心运作的、进行全量订阅测试的telegram机器人

## 最近更新(3.5.1)

3.5.1版本更新如下特性：

✨ 新增Dockerfile文件。用以支持docker平台启动。
🚗 新增一键三连测指令 /fulltest。[@Avwwww 的pr](https://github.com/AirportR/FullTclash/tree/081ce53fa1d9d804932c34f56aa18b17550e6400)
🚗 安装脚本将支持自动翻页预览脚本源代码。从自动安装改为手动确认安装。
🐛 修复速度变化的颜色快超出绘图范围问题。
✨ 新增从配置文件读取api_id、api_hash、bot_token。前往配置样例模板查看使用方法。（⚠️注意，此方式对于已生成的session文件无法覆盖。如果需要从配置生成文件，请先删除之前的。）
✨ 新增从配置文件设置速度测试的节点数量限制。[@kogekiplay 的pr](https://github.com/AirportR/FullTclash/tree/3b0d68f3047e8a6402e021cfab40a31a3231a1cb)
✨ 支持绘图水印。前往配置样例模板查看配置方法。
✨ 支持Docker启动。但需要您自行通过Dockerfile文件生成可以镜像。如果有此方面需求，请联系我或在群里反馈。
🐛 修复速度测试偶现绘图问题。[@欧阳逸洛 的pr](https://github.com/AirportR/FullTclash/tree/ae9f9e66dc31b71e0fb7da7c329cf7da03c16c54)
🐛 修复subinfo指令部分可能问题。[@kogekiplay 的pr](https://github.com/AirportR/FullTclash/tree/d8316dc461953731e754c342c2866f7ad8c19fd0)

历史更新请到TG频道查看: 

https://t.me/FullTClash

## 基本介绍

FullTclash bot 是承载其测试任务的Telegram 机器人（以下简称bot）,目前支持以clash配置文件为载体的**批量**联通性测试,支持以下测试条目:
- Netflix
- Youtube
- Disney Plus
- Bilibili
- Primevideo
- steam货币
- OpenAI(ChatGPT)
- 落地ip风险(IP欺诈度)
- 维基百科

以及HTTP延迟测试和链路拓扑测试（节点出入口分析）。

## 效果预览

流媒体测试:

![测试图片](https://upload.cc/i1/2022/09/11/fEY9zU.png)

![测试图片](https://upload.cc/i1/2022/09/11/0w2sMB.png)

## 如何开始

### 基础准备

要成功运行该项目代码，首先需要准备以下信息：

- Telegram 的api_id 、api_hash [获取地址](https://my.telegram.org/apps) 不会请Google。(部分TG账号已被拉黑，无法正常使用)

- 去 [@BotFather](https://t.me/BotFather) 那里创建一个机器人，获得该机器人的bot_token，应形如：
  
  bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
  
  这步不会请Google。

- 一个clash 核心， [下载地址](https://github.com/Dreamacro/clash/releases)。（可选，可以用/resources里默认的）

- 字体文件。（可选，可以用默认的）

### 环境准备

- Python 3.6 以上

- 以及各种相关包依赖

您可以用以下命令，在当前项目目录下运行以快速安装环境：

Windows:

```
pip install -r requirements.txt
```

Linux:

```
pip3 install -r requirements.txt
```

### 拉取源码

方法1：直接下载（不会有人不知道在哪下吧？）

方法2：使用git（Linux推荐，方便更新），首先安装git，然后拉取仓库。以下指令为 Ubuntu 发行版作示例，Windows自行解决。

```
apt install -y git && git clone https://github.com/AirportR/FullTclash.git && cd FullTclash
```

此方法在中国大陆可能需要代理加速，请自行解决。

### 获取session文件

您需要在项目文件目录下，放置一个已经登陆好的.session后缀文件，这个文件是程序生成的，形如： my_bot.session

方法1： 您可以参阅[这篇文档](https://docs.pyrogram.org/start/auth)，以快速获得后缀为 .session 的文件

方法2： 项目根目录下有一个文件名为 login.py ，可以通过指令运行它：

```
python .\login.py
```

当程序退出后即可自动生成一个名为 my_bot.session 的文件

运行后它会尝试给你输入的用户名的目标发送消息，当接收到：嗨, 我在正常工作哦！

这句话时，即可说明该session文件有效，否则无效。

## 赋予clash核心执行权限 (Linux)

Windows系统无需此操作

```
chmod +x ./resources/clash-linux-amd64
```

### 为bot进行相关配置

- 管理员配置
  
  新建一个名为config.yaml的文件，项目有模板例子名为./resources/config.yaml.example,在config.yaml中写入如下信息： 
  
  ```
  admin:
  - 12345678 # 改成自己的telegram uid
  ```

- 代理配置
  
  如果是在中国大陆地区使用，则程序需要代理才能连接上Telegram服务器。在config.yaml中写入如下信息： 
  
  ```
  #bot通讯代理
  bot:
  proxy: 127.0.0.1:7890 #替换成自己的代理地址和端口
  # 获取订阅时使用代理（可选）
  proxy: 127.0.0.1:7890 #替换成自己的代理地址和端口,注意，此配置与上面的独立分开。
  ```
- 更改clash核心

  如果您想在非Windows平台运行此程序，请在配置文件中指定对应平台的clash可执行文件：
  ```yaml
  # 以Ubuntu为例:
  clash:
    path: ./resources/clash-linux-amd64
    workpath: ./clash
  ```
### 开始启动

在项目目录下运行以下指令
Windows10:
```shell
python clash.py
```
在第二个窗口运行:
```shell
python main.py
```

Ubuntu: 
```shell
python3 clash.py
```
在第二个窗口运行:
```shell
python3 main.py
```

等待初始化操作，出现“程序已启动!”字样就说明在运行了.
运行之后和bot私聊命令：

/testurl 订阅地址(clash配置格式)
即可开始测试

/help 可查看所有命令说明

### 为程序设置进程守护(Linux)

由于Linux系统特性，关闭ssh连接后，前台程序会被关闭。您需要设置进程守护，才能在后台不间断地运行程序。具体方法Google搜索即可。

## 交流探讨

我们欢迎各方朋友提出针对性的反馈：

[TG更新发布频道](https://t.me/FullTClash)

在项目页面提出issue

## 致谢

- [SSRSpeedN部分代码灵感](https://github.com/PauperZ/SSRSpeedN)

- [流媒体解锁思路](https://github.com/lmc999/RegionRestrictionCheck)

- 以下这些上游项目:
  
  - [Clash](https://github.com/Dreamacro/clash)
  
  - [aiohttp](https://github.com/aio-libs/aiohttp)
  
  - [pyrogram](https://github.com/pyrogram/pyrogram)
  
  - [async-timeout](https://github.com/aio-libs/async-timeout)
  
  - [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
  
  - [Pillow](https://github.com/python-pillow/Pillow)
  
  - [pilmoji](https://github.com/jay3332/pilmoji)
  
  - [pyyaml](https://github.com/yaml/pyyaml)
  
  - [requests](https://github.com/psf/requests)
