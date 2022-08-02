# FullTclash

基于clash 核心运作的、进行全量订阅测试的telegram机器人

# 最近更新(3.0.1)
- 针对先前Disney+ 测试不准确的问题，现已进行判断逻辑上的重构。准确率提高了（大概吧~）

- 尝试显示流媒体解锁的地区，现已在Disney+测试项开启测试，其他测试项保持原样

- 注意到频繁地反馈测试进度会触发bot api的FloodWait，导致机器人无法发送信息。现如今反馈测试进度只会发送十次(10% 20% 30%...以此类推)，这种保护措施可有效避免触发风控



历史更新请到TG频道查看: 

https://t.me/FullTClash


# 基本介绍

FullTclash bot 是承载其测试任务的Telegram 机器人（以下简称bot）,目前支持以clash配置文件为载体的**批量**流媒体测试,支持以下流媒体测试条目:

- Netflix
  
- Youtube
  
- Disney Plus
  

以及 HTTP ping 的体感延迟测试。

# 效果预览
![测试图片](https://3o.hk/images/2022/07/15/image.png)

# 如何开始

## 基础准备

要成功运行该项目代码，首先需要准备以下信息：

- Telegram 的api_id 、api_hash [获取地址](https://my.telegram.org/apps) 不会请Google。
  
- 去 [@BotFather](https://t.me/BotFather) 那里创建一个机器人，获得该机器人的bot_token，应形如：
  
  bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
  
  这步不会请Google。
  
- 一个clash 核心， [下载地址](https://github.com/Dreamacro/clash/releases)。（可选，你可以用Releases里默认的）
  
- 字体文件。（可选，可以用默认的）
  

## 环境准备

- Python 3.5 以上
  
- aiohttp>=3.8.1
  
- async_timeout>=4.0.2
  
- beautifulsoup4>=4.11.1
  
- Pillow>=9.2.0
  
- pilmoji>=2.0.1
  
- Pyrogram>=2.0.26
  
- PyYAML>=6.0
  
- requests>=2.26.0
  

您可以用以下命令，在当前项目目录下运行以快速安装环境(Windows)：

```
pip install -r requirements.txt
```

## 获取session文件

您需要在项目文件目录下，放置一个已经登陆好的.session后缀文件，这个文件是程序生成的，形如： my_bot.seesion

方法1： 您可以参阅[这篇文档](https://docs.pyrogram.org/start/auth)，以快速获得后缀为 .session 的文件

方法2： 项目中有一个文件名为 login.py ，可以通过指令运行它：

```
python .\login.py
```

当程序退出后即可自动生成一个名为 my_bot.session 的文件


## 为bot进行相关配置

- 管理员配置

  新建一个名为config.yaml的文件，项目有模板例子名为config.yaml.example,在config.yaml中写入如下信息： 
```
  admin:
  - 12345678 # 改成自己的telegram uid
```
  

- 代理配置
  
  如果是在中国大陆地区使用，则程序需要代理才能连接上Telegram服务器。在config.yaml中写入如下信息： 
```
  proxyport: 7890
```
  
## 开始启动

在项目目录下运行以下指令

```
python .\testurl.py
```

如果什么反应都没有，请按 Ctrl + C 一次，出现“程序已启动!”字样就说明在运行了.
运行之后和bot私聊命令：
/testurl 订阅地址
即可开始测试

# 目前已知bug:

- 多人同测是是实验性功能，可能会造成部分结果不准确，单个测试不影响。
  

# 交流探讨

目前项目尚未成熟，我们欢迎各方朋友提出针对性的反馈：

[TG更新发布频道](https://t.me/FullTClash)

[TG交流群](https://t.me/+z9GvKIQUVRBiMzgx)

在项目页面提出issue

# 致谢

- [SSRSpeedN部分代码灵感](https://github.com/PauperZ/SSRSpeedN)
  
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
