FROM debian:bookworm-slim

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
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Install kubectl binary
RUN curl -sSL -o /usr/local/bin/kubectl https://dl.k8s.io/release/v1.28.2/bin/linux/amd64/kubectl \
    && chmod +x /usr/local/bin/kubectl || true

# Create isolated unprivileged system users:
# k8s-api     (uid 1001) - isolated mock kubernetes API daemon
# sentinel    (uid 1002) - public fleet sentinel web gateway & pod identity
# defense-pod (uid 1003) - isolated final challenge defense resource
RUN groupadd -g 1001 k8s-api && \
    useradd -m -u 1001 -g k8s-api -s /bin/bash k8s-api && \
    groupadd -g 1002 sentinel && \
    useradd -m -u 1002 -g sentinel -s /bin/bash sentinel && \
    groupadd -g 1003 defense-pod && \
    useradd -m -u 1003 -g defense-pod -s /bin/bash defense-pod

# Configure Nginx Reverse Proxy for Sentinel Gateway on Port 80
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
}' > /etc/nginx/sites-available/sentinel && \
    ln -s /etc/nginx/sites-available/sentinel /etc/nginx/sites-enabled/

# Set up challenge files
WORKDIR /challenge
COPY challenge/ /challenge/
COPY entrypoint.sh /challenge/entrypoint.sh

RUN chmod +x /challenge/entrypoint.sh \
    /challenge/app/server.py \
    /challenge/k8s_api/mock_k8s_server.py

# Create log files with proper user permissions
RUN touch /var/log/k8s-mock-api.log /var/log/sentinel-app.log && \
    chown k8s-api:k8s-api /var/log/k8s-mock-api.log && \
    chown sentinel:sentinel /var/log/sentinel-app.log && \
    chmod 644 /var/log/*.log

EXPOSE 80

ENTRYPOINT ["/challenge/entrypoint.sh"]
