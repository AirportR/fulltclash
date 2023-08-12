FROM ubuntu:latest

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    python3 \
    python3-pip && \
    git clone -b dev https://github.com/AirportR/FullTclash.git /app && \
    pip3 install --no-cache-dir -r requirements.txt && \
    cp resources/config.yaml.example resources/config.yaml && \
    rm -rf /var/lib/apt/lists/*

CMD ["main.py"]
ENTRYPOINT ["python3"]
