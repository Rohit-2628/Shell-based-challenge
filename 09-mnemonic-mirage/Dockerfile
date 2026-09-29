FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir Pillow

RUN useradd -m -u 1001 ctf

COPY src/ /app/src/
COPY handouts/ /app/handouts/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh /app/src/mirage_server.py && \
    touch /flag.txt && chown ctf:ctf /flag.txt

USER ctf

EXPOSE 8001

ENTRYPOINT ["/entrypoint.sh"]
