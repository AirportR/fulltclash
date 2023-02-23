FROM python:3.9-slim-buster

WORKDIR /app

RUN apt-get update && \
    apt-get install -y git && \
    git clone https://github.com/AirportR/FullTclash.git -b dev /app && \
    pip install -r requirements.txt && \
    chmod +x /app/resources/clash-linux-amd64

COPY config.yaml /app/resources/

CMD ["sh", "-c", "python3 main.py"]


