FROM debian:bookworm-slim

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    curl \
    jq \
    ca-certificates \
    procps \
    libcap2-bin \
    iproute2 \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Grant python3 capability to bind to low ports (<1024) like port 80
RUN setcap 'cap_net_bind_service=+ep' $(readlink -f $(which python3))

# Create unprivileged system users:
# vault (uid 1001) - isolated internal executive core service
# prod (uid 1002) - isolated production API gateway
RUN groupadd -g 1001 vault && \
    useradd -m -u 1001 -g vault -s /bin/bash vault && \
    groupadd -g 1002 prod && \
    useradd -m -u 1002 -g prod -s /bin/bash prod

# Set up challenge files
WORKDIR /challenge
COPY challenge/ /challenge/
COPY entrypoint.sh /challenge/entrypoint.sh

RUN chmod +x /challenge/entrypoint.sh \
    /challenge/production/app.py \
    /challenge/internal/internal_service.py

# Setup vault directory for flag
RUN mkdir -p /opt/vault && \
    chown -R vault:vault /opt/vault && \
    chmod 700 /opt/vault

# Setup production directories with strict permissions
RUN mkdir -p /opt/production && \
    chown -R prod:prod /opt/production && \
    chmod 755 /opt/production

# Restrict permissions on logs
RUN touch /var/log/internal-core.log /var/log/production-gateway.log && \
    chown vault:vault /var/log/internal-core.log && \
    chown prod:prod /var/log/production-gateway.log && \
    chmod 644 /var/log/*.log

# Only expose documented external interface (TCP/80)
EXPOSE 80

ENTRYPOINT ["/challenge/entrypoint.sh"]
