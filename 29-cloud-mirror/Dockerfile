FROM debian:bookworm-slim

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    nginx \
    curl \
    jq \
    ca-certificates \
    procps \
    iproute2 \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Create isolated system users:
# mirrorapp (uid 1001) - public image fetcher and web frontend
# metadata  (uid 1002) - isolated mock cloud metadata daemon
# storage   (uid 1003) - isolated mock object storage daemon
RUN groupadd -g 1001 mirrorapp && \
    useradd -m -u 1001 -g mirrorapp -s /bin/bash mirrorapp && \
    groupadd -g 1002 metadata && \
    useradd -m -u 1002 -g metadata -s /bin/bash metadata && \
    groupadd -g 1003 storage && \
    useradd -m -u 1003 -g storage -s /bin/bash storage

# Configure Nginx Reverse Proxy for Cloud Mirror Gateway on Port 80
RUN rm -f /etc/nginx/sites-enabled/default && \
    echo 'server {\n\
    listen 80 default_server;\n\
    listen [::]:80 default_server;\n\
    server_name _;\n\
    client_max_body_size 10M;\n\
\n\
    location / {\n\
        proxy_pass http://127.0.0.1:8000;\n\
        proxy_set_header Host $http_host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
        proxy_set_header X-Forwarded-Proto $scheme;\n\
        proxy_read_timeout 30s;\n\
    }\n\
}' > /etc/nginx/sites-available/cloud-mirror && \
    ln -s /etc/nginx/sites-available/cloud-mirror /etc/nginx/sites-enabled/

# Set up challenge files
WORKDIR /challenge
COPY challenge/ /challenge/
COPY entrypoint.sh /challenge/entrypoint.sh

RUN chmod +x /challenge/entrypoint.sh \
    /challenge/app/server.py \
    /challenge/metadata_service/metadata_server.py \
    /challenge/object_store/object_store_server.py \
    /challenge/object_store/seed_data.py

# Pre-generate mock object storage
RUN mkdir -p /var/lib/latveria-storage && \
    python3 /challenge/object_store/seed_data.py /var/lib/latveria-storage && \
    chown -R storage:storage /var/lib/latveria-storage && \
    chmod -R 755 /var/lib/latveria-storage

# Setup storage directory with strict permissions for flag
RUN mkdir -p /opt/storage && \
    chown -R storage:storage /opt/storage && \
    chmod 700 /opt/storage

# Restrict permissions on sensitive logs
RUN touch /var/log/metadata-server.log /var/log/storage-server.log /var/log/mirrorapp-server.log && \
    chown metadata:metadata /var/log/metadata-server.log && \
    chown storage:storage /var/log/storage-server.log && \
    chown mirrorapp:mirrorapp /var/log/mirrorapp-server.log && \
    chmod 600 /var/log/*.log

EXPOSE 80

ENTRYPOINT ["/challenge/entrypoint.sh"]
