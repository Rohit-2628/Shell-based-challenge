FROM debian:bookworm-slim

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    python3 \
    git \
    curl \
    jq \
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
# prod (uid 1002) - isolated production daemon runner
RUN groupadd -g 1001 developer && \
    useradd -m -u 1001 -g developer -s /bin/bash developer && \
    echo "developer:developer" | chpasswd && \
    groupadd -g 1002 prod && \
    useradd -m -u 1002 -g prod -s /bin/bash prod

# Configure OpenSSH Server
RUN mkdir -p /run/sshd && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config && \
    echo "AllowUsers developer" >> /etc/ssh/sshd_config && \
    echo "ClientAliveInterval 60" >> /etc/ssh/sshd_config && \
    echo "ClientAliveCountMax 5" >> /etc/ssh/sshd_config

# Set up challenge files
WORKDIR /challenge
COPY challenge/ /challenge/
COPY entrypoint.sh /challenge/entrypoint.sh

RUN chmod +x /challenge/entrypoint.sh \
    /challenge/workstation/setup_workstation.sh \
    /challenge/production/server.py

# Run initial setup for the developer workstation
RUN /challenge/workstation/setup_workstation.sh && \
    chown -R developer:developer /home/developer && \
    chmod 750 /home/developer

# Setup production directories with strict permissions
RUN mkdir -p /opt/production && \
    chown -R prod:prod /opt/production && \
    chmod 700 /opt/production

# Restrict permissions on sensitive logs
RUN touch /var/log/production-server.log && \
    chown prod:prod /var/log/production-server.log && \
    chmod 600 /var/log/production-server.log

EXPOSE 22

ENTRYPOINT ["/challenge/entrypoint.sh"]
