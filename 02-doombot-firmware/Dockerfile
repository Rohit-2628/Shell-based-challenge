FROM python:3.11-slim

WORKDIR /app

# Create unprivileged user
RUN useradd -m -u 1001 ctf

COPY src/c2_server.py /app/c2_server.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh /app/c2_server.py

USER ctf

EXPOSE 1338

ENTRYPOINT ["/entrypoint.sh"]
