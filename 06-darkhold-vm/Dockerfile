FROM debian:bookworm-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1001 ctf

COPY src/ /app/src/
COPY handouts/ /app/handouts/
COPY entrypoint.sh /entrypoint.sh

RUN gcc -O2 /app/src/darkhold_vm.c -o /app/src/darkhold_vm && \
    chmod +x /app/src/darkhold_vm /entrypoint.sh /app/src/darkhold_server.py

USER ctf

EXPOSE 1340

ENTRYPOINT ["/entrypoint.sh"]
