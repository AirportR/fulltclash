FROM golang:1.20.7-alpine AS builder

WORKDIR /app/fulltclash-origin
RUN apk add --no-cache git && \
    git clone https://github.com/AirportR/FullTCore.git /app/fulltclash-origin && \
    go build -ldflags="-s -w" fulltclash.go

WORKDIR /app/fulltclash-meta
RUN git clone -b meta https://github.com/AirportR/FullTCore.git /app/fulltclash-meta && \
    go build -tags with_gvisor -ldflags="-s -w" fulltclash.go


FROM python:alpine3.18

WORKDIR /app

RUN apk add --no-cache \
    git gcc g++ make libffi-dev tzdata && \
    git clone -b dev https://github.com/AirportR/FullTclash.git /app && \
    pip3 install --no-cache-dir -r requirements.txt && \
    cp resources/config.yaml.example resources/config.yaml && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    apk del gcc g++ make libffi-dev tzdata && \
    rm -f rm -f bin/*

COPY --from=builder /app/fulltclash-origin/fulltclash ./bin/fulltclash-origin
COPY --from=builder /app/fulltclash-meta/fulltclash ./bin/fulltclash-meta

CMD ["main.py"]
ENTRYPOINT ["python3"]
