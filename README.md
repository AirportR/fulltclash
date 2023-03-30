# FullTclash

基于clash 核心运作的、进行全量订阅测试的telegram机器人

## 最近更新(3.5.3)

3.5.3版本更新如下特性：

✏️3.5.3版本更新如下特性：

⚠️ emoji: True 配置写法更改为：
emoji:
 enable: true
 emoji-source: 'TwemojiLocalSource' #本地源
✨ 支持自定义测试文本， 详见config.yaml.example：bot: 
✨ 支持本地emoji pr: [@ouyangyiluo ](https://github.com/AirportR/FullTclash/commit/79a9d7e3eaf84315cf271b705c67f65cf8429c9e)。使用方法详见 config.yaml.example 。设置本地源后，启动bot即可自动下载导入。
✨ 拓扑测试中添加IP双栈检测。pr: [@mlmmlm](https://github.com/AirportR/FullTclash/commit/ddabcceb318d49196ec6d01adca0e27baa7fd993)
✨ 支持 /grant、/ungrant 通过 /grant UID1 UID2 ... 的参数方式授权/解除用户。
➕ 联通性绘图的行间距从40到60。并优化了一定的色彩，增加几个绘图标签 pr: [@mlmmlm](https://github.com/AirportR/FullTclash/commit/35a2f436d12fb648a2fc527a160a4c71f8e92b4c)
🖼 支持自定义绘图背景颜色。pr: [@mlmmlm](https://github.com/AirportR/FullTclash/commit/33bf4a393b77d95568628b3981faaa40cd2d5361)
➕ 新增是否允许缓存订阅配置项。暂不生效。
🚗 优化了很多代码。[详见](https://github.com/AirportR/FullTclash/commit/4bd47d5cf6afff93c777de1164be60d02f27881f)
🚗 优化绘图水印。pr: [@ouyangyiluo](https://github.com/AirportR/FullTclash/commit/40f7ab31c3371cb254b7b463481414a8b8896484)
🚗 优化双栈检测。pr: [@mlmmlm](https://github.com/AirportR/FullTclash/commit/9d52fec83613c1c5c4a61a056fd4aef6938a2e0f)
🐛 修复权限验证问题。[详见](https://github.com/AirportR/FullTclash/commit/d96201e840b81c90b8ba6f290911289d7279ae0d)
✨ bot发送文件到TG时会出现正在发送文件的提示。
📖 新增许多代码注释。
📖 新增关于对代码贡献提交请求的说明 pr: [@Kuroshimacat ](https://github.com/AirportR/FullTclash/commit/76f96450b7c34ff6b77fcf9ba39dcbac3d95adcd)

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

方法1：直接下载（不会有人不知道在哪下吧？）

方法2：使用git（Linux推荐，方便更新），首先安装git，然后拉取仓库。以下指令为 Ubuntu 发行版作示例，Windows自行解决。

```
apt install -y git && git clone https://github.com/AirportR/FullTclash.git && cd FullTclash
```

此方法在中国大陆可能需要代理加速，请自行解决。
### 环境准备

- Python 3.7 以上

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
### 赋予clash核心执行权限 (Linux)

Windows系统无需此操作

```
chmod +x ./resources/clash-linux-amd64
```
### 为bot进行相关配置

以下为启动bot的最低要求（如果您是新手，建议先以最低要求把bot跑起来，否则自己乱改配置容易出现不可预知的错误。）
- 管理员配置
  
  新建一个名为config.yaml的文件，项目有模板例子名为./resources/config.yaml.example,在config.yaml中写入如下信息： 
  
  ```
  admin:
  - 12345678 # 改成自己的telegram uid
  - 8765431 # 这是第二行，表示第二个管理员，没有第二个管理员就把该行删除。
  ```

- 代理配置
  
  如果是在中国大陆地区使用，则程序需要代理才能连接上Telegram服务器。在config.yaml中写入如下信息： 
  
  ```
  #bot通讯代理
  bot:
   proxy: 127.0.0.1:7890 #socks5 替换成自己的代理地址和端口
  # 获取订阅时使用代理（可选）
  proxy: 127.0.0.1:7890 #http 替换成自己的代理地址和端口,注意，此配置与上面的独立分开。
  ```

  
### 获取session文件

您需要在项目文件目录下，放置一个已经登陆好的.session后缀文件，这个文件是程序生成的，形如： my_bot.session

>方法1： 您可以参阅[这篇文档](https://docs.pyrogram.org/start/auth)，以快速获得后缀为 .session 的文件

>方法2： 项目根目录下有一个文件名为 login.py ，可以通过指令运行它：

```
python .\login.py
```

当程序退出后即可自动生成一个名为 my_bot.session 的文件

运行后它会尝试给你输入的用户名的目标发送消息，当接收到：嗨, 我在正常工作哦！

这句话时，即可说明该session文件有效，否则无效。
>方法3：可以直接在配置文件config.yaml中配置，这样程序启动后会自动读取配置文件里面的值来生成session文件(要求一定要正确)。
```yaml
#配置文件示例，注意缩进要正确
bot:
 api_id: 123456
 api_hash: 123456ABCDefg
 bot_token: 123456:ABCDefgh123455
```
如果启动后无法验证，请删除生成的mybot.session文件，此时的文件是坏的，不可用，如果不删除程序会一直使用坏的文件，不会重新生成。然后重新启动。
### 开始启动
配置好后，在项目目录下运行以下指令

>Windows:
```shell
python main.py
```

>Ubuntu(Linux):
```shell
python3 main.py
```

等待初始化操作，出现“程序已启动!”字样就说明在运行了.
运行之后和bot私聊命令：

/testurl 订阅地址(clash配置格式)
即可开始测试

/help 可查看所有命令说明
### Docker启动
教程文档待更新
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
## 如何给本项目做贡献：
1. 在本项目的主GitHub仓库进行fork，你可以只fork dev的分支。
2. 在你的计算机上使用git clone来下载你fork后的仓库
3. 在下载好的进行修改
4. 执行git add .（请不要忘记句号！！！）
5. 执行git commit，并输入你做出的更改
6. 回到你的仓库，发起pr请求，等待下一步（通过/驳回/修改）

如果不这样做可能会：
1. 仓库维护者看到的是一片绿色加号，根本不知道你改了什么
2. 你的操作会很麻烦，可能还会改错文件
3. 维护者很难看懂你都干了些什么
