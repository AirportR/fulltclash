# FullTclash

基于clash 核心运作的、进行全量订阅测试的telegram机器人

# 最近更新(3.3.0 大更新)
- 加入控制面板。 在进行流媒体测试的时候，会先要求用户选择想要的测试项，最后点击提交。这种设计非常灵活地给每项任务动态地调节测试内容。

- 加入任务队列机制。自经历多人同测功能失败后，不少使用者对同一时间只能测一个任务感到无奈，因此想了个折中办法，即对所有任务都进行接收，然后放入到队列这种数据结构中，进行排队，轮到该任务就会自动开始测试。

- 管理员权限向下继承。在我们的思维中，管理员作为最高权限者，理应对所有的命令都有执行权限。但在实际中并非如此，首次使用，需要管理员自己给自己授予用户权限，这种反人类的设计在该版本中已被优化。现如今管理员默认拥有用户权限。

- 在奈飞解锁测试项中，注意到解锁类型有原生解锁和dns解锁两大类型，因此在生成图片中新增显示解锁的类型。

- login.py 文件移动。 在搭建中，注意到放在 ./libs/ 下的 login.py 文件生成的session文件默认在 ./libs/ 文件夹下，为照顾部分搭建能力不足的使用者，现如今把该文件移到了项目根目录，以此生成的login.py文件默认在项目根目录，用户无需再手动移动session文件

- 修改了 README.md 的部分文档错误


历史更新请到TG频道查看: 

https://t.me/FullTClash


# 基本介绍

FullTclash bot 是承载其测试任务的Telegram 机器人（以下简称bot）,目前支持以clash配置文件为载体的**批量**流媒体测试,支持以下流媒体测试条目:

- Netflix
  
- Youtube
  
- Disney Plus

- Bilibili

- Dazn
  

以及clash 延迟测试和链路拓扑测试（节点出入口分析）。

# 效果预览
流媒体测试:

![测试图片](https://upload.cc/i1/2022/09/11/fEY9zU.png)

![测试图片](https://upload.cc/i1/2022/09/11/0w2sMB.png)

# 如何开始

## 基础准备

要成功运行该项目代码，首先需要准备以下信息：

- Telegram 的api_id 、api_hash [获取地址](https://my.telegram.org/apps) 不会请Google。
  
- 去 [@BotFather](https://t.me/BotFather) 那里创建一个机器人，获得该机器人的bot_token，应形如：
  
  bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
  
  这步不会请Google。
  
- 一个clash 核心， [下载地址](https://github.com/Dreamacro/clash/releases)。（可选，可以用/resources里默认的）
  
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

您需要在项目文件目录下，放置一个已经登陆好的.session后缀文件，这个文件是程序生成的，形如： my_bot.session

方法1： 您可以参阅[这篇文档](https://docs.pyrogram.org/start/auth)，以快速获得后缀为 .session 的文件

方法2： 项目中./libs文件夹下有一个文件名为 login.py ，可以通过指令运行它：

```
python .\login.py
```
当程序退出后即可自动生成一个名为 my_bot.session 的文件

运行后它会尝试给你输入的用户名的目标发送消息，当接收到：嗨, 我在正常工作哦！

这句话时，即可说明该session文件有效，否则无效。

## 赋予clash核心执行权限(Linux amd64)

Windows系统无需此操作
```
chmod +x ./resources/clash-linux-amd64
```


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
python .\main.py
```

如果什么反应都没有，请按 Ctrl + C 一次，出现“程序已启动!”字样就说明在运行了.
运行之后和bot私聊命令：

/testurl 订阅地址(clash配置格式)
即可开始测试

/help 可查看所有命令说明

  

# 交流探讨

我们欢迎各方朋友提出针对性的反馈：

[TG更新发布频道](https://t.me/FullTClash)

在项目页面提出issue

# 致谢

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
