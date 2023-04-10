RUN apt-get update && \
    apt-get install -y --no-install-recommends git=2.25.1 && \
    git clone https://github.com/AirportR/FullTclash.git /app && \
    pip install -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app/
COPY config.yaml ./resources/

ENTRYPOINT ["sh", "-c", "python3 main.py"]


