FROM python:3.11-slim

WORKDIR /app

# Create unprivileged user
RUN useradd -m -u 1001 ctf

COPY src/embassy_relay.py /app/embassy_relay.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh /app/embassy_relay.py

USER ctf

EXPOSE 8042

ENTRYPOINT ["/entrypoint.sh"]
