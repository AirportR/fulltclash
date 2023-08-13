FROM golang:1.21.0-alpine3.18 AS builder

WORKDIR /app

RUN apk add --no-cache git && \
    git clone https://github.com/AirportR/FullTCore.git /app && \
    go build -ldflags="-s -w" fulltclash.go

FROM python:3.10.12-alpine3.18

WORKDIR /app

RUN apk add --no-cache git && \
    git clone -b dev https://github.com/AirportR/FullTclash.git /app && \
    pip3 install --no-cache-dir -r requirements.txt && \
    rm -f rm -f bin/* && \
    cp resources/config.yaml.example resources/config.yaml

COPY --from=builder /app/fulltclash ./bin/

CMD ["main.py"]
ENTRYPOINT ["python3"]
