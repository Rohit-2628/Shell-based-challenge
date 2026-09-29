FROM python:3.11-slim

WORKDIR /app

RUN useradd -m -u 1001 ctf

COPY src/ /app/src/
COPY handouts/ /app/handouts/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh /app/src/golem_server.py

USER ctf

EXPOSE 1341

ENTRYPOINT ["/entrypoint.sh"]
