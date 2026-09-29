FROM debian:bookworm-slim

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    python3 \
    nginx \
    curl \
    jq \
    tar \
    gzip \
    ca-certificates \
    procps \
    nano \
    vim-tiny \
    less \
    iproute2 \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Create system users:
# developer (uid 1001) - workstation user
# registry (uid 1002) - isolated container registry daemon runner
# vault (uid 1003) - isolated internal orbital vault daemon runner
RUN groupadd -g 1001 developer && \
    useradd -m -u 1001 -g developer -s /bin/bash developer && \
    echo "developer:developer" | chpasswd && \
    groupadd -g 1002 registry && \
    useradd -m -u 1002 -g registry -s /bin/bash registry && \
    groupadd -g 1003 vault && \
    useradd -m -u 1003 -g vault -s /bin/bash vault

# Configure OpenSSH Server
RUN mkdir -p /run/sshd && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config && \
    echo "AllowUsers developer" >> /etc/ssh/sshd_config && \
    echo "ClientAliveInterval 60" >> /etc/ssh/sshd_config && \
    echo "ClientAliveCountMax 5" >> /etc/ssh/sshd_config

# Configure Nginx Reverse Proxy for Registry Gateway on Port 80
RUN rm -f /etc/nginx/sites-enabled/default && \
    echo 'server {\n\
    listen 80 default_server;\n\
    listen [::]:80 default_server;\n\
    server_name _;\n\
    client_max_body_size 10M;\n\
\n\
    location /api/v1/vault/ {\n\
        proxy_pass http://127.0.0.1:8080;\n\
        proxy_set_header Host $http_host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
        proxy_set_header X-Forwarded-Proto $scheme;\n\
    }\n\
\n\
    location / {\n\
        proxy_pass http://127.0.0.1:5000;\n\
        proxy_set_header Host $http_host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
        proxy_set_header X-Forwarded-Proto $scheme;\n\
        proxy_read_timeout 60s;\n\
    }\n\
}' > /etc/nginx/sites-available/registry-gateway && \
    ln -s /etc/nginx/sites-available/registry-gateway /etc/nginx/sites-enabled/

# Set up challenge files
WORKDIR /challenge
COPY challenge/ /challenge/
COPY entrypoint.sh /challenge/entrypoint.sh

RUN chmod +x /challenge/entrypoint.sh \
    /challenge/workstation/setup_workstation.sh \
    /challenge/registry/registry_server.py \
    /challenge/registry/generate_seed_data.py \
    /challenge/vault/server.py

# Pre-generate registry storage
RUN mkdir -p /var/lib/latveria-registry && \
    python3 /challenge/registry/generate_seed_data.py /var/lib/latveria-registry && \
    chown -R registry:registry /var/lib/latveria-registry && \
    chmod -R 755 /var/lib/latveria-registry

# Run initial setup for the developer workstation
RUN /challenge/workstation/setup_workstation.sh && \
    chown -R developer:developer /home/developer && \
    chmod 750 /home/developer

# Setup vault directory with strict permissions
RUN mkdir -p /opt/vault && \
    chown -R vault:vault /opt/vault && \
    chmod 700 /opt/vault

# Restrict permissions on sensitive logs
RUN touch /var/log/vault-server.log /var/log/registry-server.log && \
    chown vault:vault /var/log/vault-server.log && \
    chown registry:registry /var/log/registry-server.log && \
    chmod 600 /var/log/vault-server.log /var/log/registry-server.log

EXPOSE 80 22

ENTRYPOINT ["/challenge/entrypoint.sh"]
