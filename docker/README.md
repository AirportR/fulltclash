# 使用Docker安装

> 这能让你在Windows、Mac、Linux、openwrt、Nas几乎任何支持Docker(目前仅Amd64和Arm64)的环境下使用此项目！

## 创建配置文件
新建配置文件保存目录`mkdir /etc/FullTclash`
下载并编辑配置文件
```
wget -O /etc/FullTclash/config.yaml https://raw.githubusercontent.com/AirportR/FullTclash/dev/resources/config.yaml.example
```
修改 config.yaml (path是必须修改的配置,不能使用默认的)
```
clash:
 path: './bin/fulltclash-origin'
 branch: origin
```
或者 [Meta内核](https://github.com/AirportR/FullTCore/tree/meta)
```
clash:
 path: './bin/fulltclash-meta'
 branch: meta
```

## 部署


### 拉取镜像

> 镜像可选dev或者alpine，dev是通过Debian构建的

```bash
docker pull ghcr.io/airportr/fulltclash:dev
```

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
   -e nospeed=true \
   -e s5_proxy=127.0.0.1:7890 \
   -e http_proxy=127.0.0.1:7890 \
   --network=host \
   --restart always \
   ghcr.io/airportr/fulltclash:dev
```

#### 挂载配置文件启动(推荐)

```bash
docker run -itd \
   --name=fulltclash \
   --network=host \
   --restart=always \
   -v /etc/fulltclash/config.yaml:/app/resources/config.yaml \
   ghcr.io/airportr/fulltclash:dev
```

### docker-compose(推荐)

```bash
# 安装 docker-compose
# curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
# chmod +x /usr/local/bin/docker-compose
wget -N https://raw.githubusercontent.com/AirportR/FullTclash/dev/docker/docker-compose.yml

# 启动
docker-compose up -d
# 停止
docker-compose down
```

查看日志
```
docker exec -it fulltclash tail -f /var/log/fulltclash.log
```
更新版本
```
docker exec -it fulltclash bash /app/docker/update.sh
```
重启程序
```
docker exec -it fulltclash supervisorctl restart fulltclash
```