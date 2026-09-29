FROM python:3.11-slim

WORKDIR /app

RUN useradd -m -u 1001 ctf

COPY src/ /app/src/
COPY handouts/ /app/handouts/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh /app/src/tribunal_server.py

USER ctf

EXPOSE 5001 1342

ENTRYPOINT ["/entrypoint.sh"]
