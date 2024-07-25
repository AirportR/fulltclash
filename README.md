
<div align="center">
    <h1> FullTClash</h1>
    <p>🤖 节点质量检测的Telegram机器人 </p>
    <p><a href="https://github.com/AirportR/fulltclash/blob/dev/README-EN.md">English</a>&nbsp &nbsp 简体中文</p>
    <a href="https://fulltclash.gitbook.io/fulltclash-doc"><img src="https://img.shields.io/static/v1?message=doc&color=blue&logo=micropython&label=FullTClash"></a> 
    <img src="https://img.shields.io/github/license/AirportR/fulltclash">
    <a href="https://app.codacy.com/gh/AirportR/fulltclash/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade"><img src="https://app.codacy.com/project/badge/Grade/389b2787eb7647dfad486ccaa70eabf4"></a>
    <a href="https://github.com/AirportR/fulltclash/issues"><img src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat"></a>
    <br>
    <img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/airportr/fulltclash">
    <img alt="Docker Image Size" src="https://img.shields.io/docker/image-size/airportr/fulltclash">
    <br>
    <a href="https://github.com/AirportR/fulltclash/"><img src="https://img.shields.io/github/stars/AirportR/fulltclash?style=social"></a>
	<a href = "https://t.me/FullTclash"><img src="https://img.shields.io/static/v1?style=social&logo=telegram&label=channel&message=channel" ></a>
	<br>
	<br>
</div>


## 介绍

🚗快速批量检测**Clash配置**文件里节点的质量，帮助你筛选优质节点✌️，
目前支持以下测试条目:
1. Netflix 
2. Youtube Premium
3. DisneyPlus 
4. Bilibili解锁 
5. OpenAI(ChatGPT) 
6. 落地ip风险(IP欺诈度) 
7. 维基百科
8. 微软Copilot
9. Claude
10. 落地DNS区域检测
11. Spotify 
12. SSH 22端口封禁检测
13. Tiktok

此外还有：

1. HTTP延迟测试
2. 链路拓扑测试（节点出入口分析）
3. 下行速度测试

## 主要功能

* asyncio异步支持
* 订阅管理
* 测试结果绘图
* 权限控制
* 文档支持
* TG MTProto通信(Pyrogram)
* 规则系统
* 支持Docker
* 命令行支持
* 日志输出
* 插件扩展
* 自由定制化配置


## 分支说明
* [master](https://github.com/AirportR/fulltclash/tree/master) 主分支，主打稳定。  
* [backend](https://github.com/AirportR/fulltclash/tree/backend) 纯后端代码，无前端BOT，意味着需要额外的bot作主端。  
* [dev](https://github.com/AirportR/fulltclash/tree/dev) 开发进度最前沿。  
* [old](https://github.com/AirportR/fulltclash/tree/dev) 依靠调用原版Clash Restful API进行测试。可随意更换内核，但已停止新功能开发。  

## 支持协议

| 出站协议           | Clash | Mihomo(Clash.Meta) |
|----------------|-------|--------------------|
| SOCKS (4/4a/5) | √     | √                  |
| HTTP(S)        | √     | √                  |
| Shadowsocks    | √     | √                  |
| VMess          | √     | √                  |
| Trojan         | √     | √                  | 
| Snell          | √     | √                  | 
| VLESS          |       | √                  |
| TUIC           |       | √                  |
| Hysteria       |       | √                  |
| Hysteria2      |       | √                  |
| Wireguard      |       | √                  |
| ShadowsocksR   | √     | √                  |
----------------------
本项目默认使用mihomo内核。
## 使用文档

可以在 [这里](https://fulltclash.gitbook.io/fulltclash-doc) 找到fulltclash的使用文档。
## 效果预览

流媒体测试:

![测试图片](https://github.com/AirportR/fulltclash/blob/dev/resources/image/test_example.png)

![测试图片](https://github.com/AirportR/fulltclash/blob/dev/resources/image/topo_example.jpg)

## 如何开始

### 基础准备

要成功运行该Telegram 机器人，首先需要准备以下信息：

- Telegram 的api_id 、api_hash [获取地址](https://my.telegram.org/apps) 不会请Google。(部分IP已被拉黑，无法正常申请成功，请尝试更换干净IP)  

- 去 [@BotFather](https://t.me/BotFather) 那里创建一个机器人，获得该机器人的bot_token，应形如：  
  
  bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
  
  这步不会请Google。

### 拉取源码
方法1：直接下载（不会有人不知道在哪下吧？）\
方法2：使用git（Linux推荐，方便更新），首先安装git，然后拉取仓库。以下指令为 Ubuntu 发行版作示例，Windows自行解决。
```shell
apt install -y git && git clone https://github.com/AirportR/fulltclash.git && cd fulltclash
```
此方法在中国大陆可能需要代理加速，请自行解决。
### 环境准备

- Python 版本范围 (3.9 ~ 3.11)
- 以及各种相关包依赖  

您可以用以下命令，在当前项目目录下运行以快速安装环境：

```shell
pip install -r requirements.txt
```
### 为bot进行相关配置
以下为启动bot的最低要求（如果您是新手，建议先以最低要求把bot跑起来，否则自己乱改配置容易出现不可预知的错误。）

新建一个名为config.yaml的文件，放在./resources下，项目有模板例子名为./resources/config.yaml.example,在config.yaml中写入如下信息： 
  

  
- bot相关配置  
  ```yaml
  bot:
   api_id: 123456 #改成自己的api_id
   api_hash: 123456ABCDefg #改成自己的api_hash
   bot_token: 123456:ABCDefgh123455  # bot_token, 从 @BotFather 获取
   # 如果是在中国大陆地区使用，则程序需要代理才能连接上Telegram服务器。写入如下信息：
   proxy: 127.0.0.1:7890 #必须是socks5类型 替换成自己的代理地址和端口
  ```

- 代理客户端路径配置
  
  从3.6.8开始，初次启动将自动下载以下(Windows,MacOS,Linux)(x86_64,arm64)的二进制文件，无需配置。
  
  当然如果您想手动下载， 请自行前往以下网址获取: 
  https://github.com/AirportR/FullTCore/releases \
  下载解压后可以放到 ./bin/ 目录下，比如文件名为 FullTCore ，下面的配置文件这样写：
  ```yaml
  clash:
   path: "./bin/FullTCore" #这里改成代理客户端文件路径
  ```
  Windows系统名字后缀名.exe要加上，其他类Unix系统不需要加后缀名。
- 管理员配置（可选）

  从3.6.11版本开始，bot在首次启动时会将接收到的第一条消息的发送者作为管理员，一般无需手动配置，除非您想设置多个管理员：
  ```yaml
  admin:
  - 12345678 # 改成自己的telegram uid
  - 8765431 # 这是第二行，表示第二个管理员，没有第二个管理员就把该行删除。
  ```
- HTTP代理配置（可选）  
  
  如果是在中国大陆地区使用，可能部分网址无法直接连接。可在config.yaml中写入如下信息，下载资源文件时将自动应用该项配置： 
  
  ```
  # 获取订阅时使用代理（可选）
  proxy: 127.0.0.1:7890 #http代理类型 替换成自己的代理地址和端口,注意，此配置与上面的独立分开。
  ```
  
- 自定义buildtoken(可选)

  **个人使用请直接跳过这条**

  buildtoken是构建 ./bin/FullTCore(.exe) 代理客户端二进制文件的编译Token，此token为数据加密密钥，一般来说，用项目自带的编译token在本地运行不会有任何问题，但是如果您选择自己编译并且更改了 build.key文件，则主端需要改变默认配置，以此用到编译token，这个token需要写入到配置文件里，供Bot加密信息。
  ```yaml
  buildtoken: 12345678ABCDEFG
  ```
### 获取session文件（可选）

您需要在项目文件目录下，放置一个已经登陆好的.session后缀文件，这个文件是程序生成的，是Telegram的登录凭据，形如： my_bot.session
* 方法1：

  可以直接在配置文件config.yaml中配置，这样程序启动后会自动读取配置文件里面的值来生成session文件(要求一定要正确)。
  ```yaml
  #配置文件示例，注意缩进要正确
  bot:
   api_id: 123456
   api_hash: 123456ABCDefg
   bot_token: 123456:ABCDefgh123455
  ```
* 方法2： 您可以参阅[这篇文档](https://docs.pyrogram.org/start/auth)，以快速获得后缀为 .session 的文件

* 方法3： 项目的 ./utils/tool/ 目录下有一个文件名为 login.py ，可以通过指令运行它：
  ```
  python login.py
  ```

  当程序退出后即可自动生成一个名为 my_bot.session 的文件 ，之后将它移动到项目根目录。
  运行后它会尝试给你输入的用户名的目标发送消息，当接收到：**嗨, 我在正常工作哦！**

  这句话时，即可说明该session文件有效，否则无效。

如果启动后无法验证，请删除生成的mybot.session文件，此时的session登录令牌是不可用的，如果不删除程序会一直使用坏的文件，不会重新生成。

### 开始启动
配置好后，在项目目录下运行以下指令
```shell
python3 main.py
```

等待初始化操作， 等待初始化完毕后进入运行状态了，运行之后和bot私聊指令：
>/help 可查看所有命令说明

>/testurl <订阅地址> (Clash配置格式) 即可开始测试

### 代理客户端编译(高级)
FullTClash有专用的代理客户端，存放在 ./bin/下。初次启动会自动帮您下载（仅限win、linux、darwin）对应平台的二进制文件。

文件的压缩包格式为: **FullTCore\_{版本号}\_{平台}\_{CPU架构}.{压缩包后缀}**

没有所用架构？
如果发现没有自动下载，说明没有在仓库中找到您所用架构的二进制文件，比如mips架构，那么您需要自行编译。

在 [此仓库](https://github.com/AirportR/FullTCore) 下有一源码文件为 fulltclash.go ，您需要将该文件自行用Golang编译器编译成二进制文件。


编译完成覆盖原文件即可 ，如果操作难度太大，可以发起issue详谈。
### Docker启动
[./docker/ 目录](https://github.com/AirportR/fulltclash/tree/dev/docker)
### 持久化运行
自行Google搜索即可
### 控制台测试
您可以在本机的控制台使用命令行的方式进行测试，但仅支持基本测试功能：
```shell
python ./utils/tool/console.py -h
```
## 交流探讨
我们欢迎各方朋友提出针对性的反馈：
- [TG更新发布频道](https://t.me/FullTClash)  
- 在项目页面提出issue

## 项目贡献：
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
自从FullTClash的3.5.8版本起，支持前后端模式，我们把后端部分单独分离，使之可以让前端的bot运行环境与后端运行的环境不在同一台机器上，在当时Clash并没有提供符合本项目的特性，再加上FullTClash仅仅只需要其中出站功能，所以不得已进行一些改动。事实上，FullTClash的old分支是依靠Clash提供的Restful API运行的，现在已不再维护。  
3. 什么是Telegram UID\
Telegram官方并没有承认UID的说法，但确实存在于Telegram中。每一个TG用户都存在一个唯一的身份ID，这个在官方的TG客户端是查询不到的。Bot依靠UID确定管理员身份，至于如何获取Google搜索即可。  
4. 是否有一键部署脚本\
目前只有Docker部署脚本，期待你的贡献！  
5. FullTClash名字来源于 Full Test base on Clash。\
后端部分使用[Clash项目](https://github.com/Dreamacro/clash)(现在亦可称之为[mihomo](https://github.com/MetaCubeX/mihomo))相关代码作为出站代理。
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