FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pil \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1001 ctf

COPY src/ /app/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh /app/server.py

USER ctf

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
