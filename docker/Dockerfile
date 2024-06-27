FROM python:3.11.9-alpine3.20 AS compile-image

RUN apk add --no-cache \
    gcc g++ make libffi-dev libstdc++ gcompat libgcc build-base py3-pybind11-dev abseil-cpp-dev re2-dev ca-certificates

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
ADD https://raw.githubusercontent.com/AirportR/FullTclash/backend/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt && \
    pip3 install --no-cache-dir supervisor

FROM python:3.11.9-alpine3.20

ARG GIT_Branch
ENV GIT_Branch=$GIT_Branch
ENV TZ=Asia/Shanghai
ENV bind=0.0.0.0:8765
ENV token=fulltclash
ENV branch=origin
ENV core=4
ENV SHELL=/bin/bash
ENV LANG C.UTF-8

WORKDIR /app

RUN apk add --no-cache \
    git tzdata curl jq wget bash nano && \
    git clone -b $GIT_Branch --single-branch --depth=1 https://github.com/AirportR/FullTclash.git /app && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    echo "00 6 * * * bash /app/docker/update.sh" >> /var/spool/cron/crontabs/root && \
    mkdir /etc/supervisord.d && \
    mv /app/docker/supervisord.conf /etc/supervisord.conf && \
    mv /app/docker/fulltclash.conf /etc/supervisord.d/fulltclash.conf && \
    chmod +x /app/docker/fulltcore.sh && \
    bash /app/docker/fulltcore.sh && \
    sed -i 's/ash/bash/g' /etc/passwd && \
    chmod +x /app/docker/update.sh && \
    chmod +x /app/docker/docker-entrypoint.sh

COPY --from=compile-image /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=compile-image /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT ["/app/docker/docker-entrypoint.sh"]