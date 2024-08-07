FROM airportr/fulltclash:debian AS compile-image

FROM python:3.11.9-slim-bookworm

ARG GIT_Branch
ENV GIT_Branch=$GIT_Branch
ENV TZ=Asia/Shanghai
ENV admin=12345678
ENV api_id=123456
ENV api_hash=ABCDEFG
ENV bot_token=123456:ABCDEFG
ENV branch=origin
ENV core=4
ENV startup=1124
ENV speednodes=300
ENV speedthread=4
ENV nospeed=true

WORKDIR /app

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    git tzdata curl wget jq bash nano cron && \
    git clone -b $GIT_Branch --single-branch --depth=1 https://github.com/AirportR/FullTclash.git /app && \
    git clone --single-branch --depth=1 https://github.com/twitter/twemoji.git /app/resources/emoji/twemoji && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    mkdir /etc/supervisord.d && \
    mv /app/docker/supervisord.conf /etc/supervisord.conf && \
    mv /app/docker/fulltclash.conf /etc/supervisord.d/fulltclash.conf && \
    chmod +x /app/docker/fulltcore.sh && \
    /app/docker/fulltcore.sh && \
    cp /app/docker/crontab /etc/cron.d/crontab && \
    chmod 0644 /etc/cron.d/crontab && \
    /usr/bin/crontab /etc/cron.d/crontab && \
    chmod +x /app/docker/update.sh && \
    chmod +x /app/docker/docker-entrypoint.sh && \
    rm -rf /var/lib/apt/lists/*

COPY --from=compile-image /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=compile-image /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT ["/app/docker/docker-entrypoint.sh"]
