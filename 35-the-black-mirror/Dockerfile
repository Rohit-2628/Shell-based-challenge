FROM python:3.11-slim

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install required Python packages
RUN pip install --no-cache-dir flask requests

# Create unprivileged runtime user
RUN groupadd -g 1000 latveria && \
    useradd -u 1000 -g latveria -m -s /bin/bash latveria

WORKDIR /app

# Copy challenge files
COPY challenge/ /app/challenge/
COPY entrypoint.sh /app/entrypoint.sh

# Set directory permissions
RUN mkdir -p /tmp && \
    chown -R latveria:latveria /app /tmp && \
    chmod +x /app/entrypoint.sh /app/challenge/flag_service/flag_server.py /app/challenge/internal_protocol/daemon.py /app/challenge/next_stage/vault.py /app/challenge/web_proxy/app.py

USER latveria

EXPOSE 80

ENTRYPOINT ["/app/entrypoint.sh"]
