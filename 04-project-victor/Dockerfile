FROM python:3.11-slim

WORKDIR /app

# Create unprivileged user
RUN useradd -m -u 1001 ctf

COPY src/victor_advisor.py /app/victor_advisor.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh /app/victor_advisor.py

USER ctf
ENV HTTP_PORT=5004
EXPOSE 5004

ENTRYPOINT ["/entrypoint.sh"]

