# 使用Docker安装

> 这能让你在Windows、Mac、Linux、openwrt、Nas几乎任何支持Docker(目前仅Amd64和Arm64)的环境下使用此项目！

## 创建配置文件

新建配置文件保存目录`mkdir /etc/fulltclash`
下载并编辑配置文件

```bash
wget -O /etc/fulltclash/config.yaml https://raw.githubusercontent.com/AirportR/fulltclash/dev/resources/config.yaml.example
```

修改 config.yaml (path是必须修改的配置,不能使用默认的)

```bash
clash:
 path: './bin/fulltclash-origin'
 branch: origin
```

或者 [Meta内核](https://github.com/AirportR/FullTCore/tree/meta)

```bash
clash:
 path: './bin/fulltclash-meta'
 branch: meta
```

## 部署

### 拉取镜像

```bash
docker pull airportr/fulltclash:latest
```

镜像还可以选择以下标签，其中 `latest` 标签是基于 `debian` `dev分支`构建

- debian-dev
- alpine-dev
- debian-master
- alpine-master

### docker

#### 快速启动

> 删除容器前请备份配置文件`docker cp fulltclash:/app/resources/config.yaml $PWD`

```bash
docker run -idt \
   --name fulltclash \
   -e admin=12345678 \
   -e api_id=123456 \
   -e api_hash=ABCDEFG \
   -e bot_token=123456:ABCDEFG \
   -e branch=origin \
   -e core=4 \
   -e startup=1124 \
   -e speedthread=4 \
   -e nospeed=false \
   -e s5_proxy=127.0.0.1:7890 \
   -e http_proxy=127.0.0.1:7890 \
   --network=host \
   --restart always \
   airportr/fulltclash:latest
```

#### 挂载配置文件启动(推荐)

```bash
docker run -itd \
   --name=fulltclash \
   --network=host \
   --restart=always \
   -v /etc/fulltclash/config.yaml:/app/resources/config.yaml \
   airportr/fulltclash:latest
```

### docker-compose(推荐)

```bash
# 安装 docker-compose
# curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
# chmod +x /usr/local/bin/docker-compose
wget -N https://raw.githubusercontent.com/AirportR/fulltclash/dev/docker/docker-compose.yml

# 启动
docker-compose up -d
# 停止
docker-compose down
```

查看日志

```bash
docker exec -it fulltclash tail -f /var/log/fulltclash.log
```

更新版本

```bash
docker exec -it fulltclash bash /app/docker/update.sh
```

重启程序

```bash
docker exec -it fulltclash supervisorctl restart fulltclash
```

进入容器

```bash
docker exec -it fulltclash bash
```

退出容器

`root@deeb9eaf66aa:/app# exit`
