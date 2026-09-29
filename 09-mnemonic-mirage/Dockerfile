FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pil \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1001 ctf

COPY src/ /app/src/
COPY handouts/ /app/handouts/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh /app/src/mirage_server.py

USER ctf

EXPOSE 8001

ENTRYPOINT ["/entrypoint.sh"]
