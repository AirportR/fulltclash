# 使用Docker安装

> 这能让你在Windows、Mac、Linux、openwrt、Nas几乎任何支持Docker的环境下使用此项目！

## 1.创建配置文件
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

## 构建Docker镜像

### 下载Dockerfile
wget -N https://raw.githubusercontent.com/AirportR/FullTclash/dev/docker/Dockerfile

### 构建镜像
```
docker build -t fulltclash:dev .
```

启动
```
docker run -itd --name=fulltclash --restart=always -v /etc/FullTclash/config.yaml:/app/resources/config.yaml fulltclash:dev
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