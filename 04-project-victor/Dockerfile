FROM python:3.11-slim

WORKDIR /app

# Create unprivileged user
RUN useradd -m -u 1001 ctf

COPY src/victor_advisor.py /app/victor_advisor.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh /app/victor_advisor.py

USER ctf

EXPOSE 5000 1339

ENTRYPOINT ["/entrypoint.sh"]
