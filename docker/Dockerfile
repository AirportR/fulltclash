FROM golang:1.20.7-bookworm AS build-core

WORKDIR /app/fulltclash-origin
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    git && \
    git clone https://github.com/AirportR/FullTCore.git /app/fulltclash-origin && \
    go build -ldflags="-s -w" fulltclash.go

WORKDIR /app/fulltclash-meta
RUN git clone -b meta https://github.com/AirportR/FullTCore.git /app/fulltclash-meta && \
    go build -tags with_gvisor -ldflags="-s -w" fulltclash.go && \
    mkdir /app/FullTCore-file && \
    cp /app/fulltclash-origin/fulltclash /app/FullTCore-file/fulltclash-origin && \
    cp /app/fulltclash-meta/fulltclash /app/FullTCore-file/fulltclash-meta

FROM python:3.9.18-slim-bookworm AS compile-image

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    gcc g++ make ca-certificates

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
ADD https://raw.githubusercontent.com/AirportR/FullTclash/dev/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt && \
    pip3 install --no-cache-dir supervisor

FROM python:3.9.18-slim-bookworm

WORKDIR /app

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    git tzdata curl jq bash nano cron && \
    git clone -b dev --single-branch --depth=1 https://github.com/AirportR/FullTclash.git /app && \
    cp resources/config.yaml.example resources/config.yaml && \
    rm -f /etc/localtime && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    echo "00 6 * * * bash /app/docker/update.sh" >> /var/spool/cron/crontabs/root && \
    mkdir /etc/supervisord.d && \
    mv /app/docker/supervisord.conf /etc/supervisord.conf && \
    mv /app/docker/fulltclash.conf /etc/supervisord.d/fulltclash.conf && \
    chmod +x /app/docker/docker-entrypoint.sh && \
    rm -rf /var/lib/apt/lists/* && \
    rm -f /app/bin/*

COPY --from=compile-image /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=compile-image /opt/venv /opt/venv
COPY --from=build-core /app/FullTCore-file/* ./bin/

ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT ["/app/docker/docker-entrypoint.sh"]
