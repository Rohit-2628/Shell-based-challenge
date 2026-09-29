FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    cron \
    procps \
    curl \
    less \
    nano \
    vim-tiny \
    iproute2 \
    net-tools \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create system users:
# relayop  (uid 1001) - public SSH login user, displayed as 'operator'
# relaydmn (uid 1002) - isolated internal relay daemon runner
RUN groupadd -g 1101 relayop && \
    useradd -m -u 1101 -g relayop -s /bin/bash -c "Relay Operator" operator && \
    echo "operator:operator" | chpasswd && \
    groupadd -g 1102 relaydmn && \
    useradd -m -u 1102 -g relaydmn -s /bin/bash relaydmn

# Configure OpenSSH Server: password auth, no root login, operator only
RUN mkdir -p /run/sshd && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config && \
    echo "AllowUsers operator" >> /etc/ssh/sshd_config && \
    echo "ClientAliveInterval 60" >> /etc/ssh/sshd_config && \
    echo "ClientAliveCountMax 5" >> /etc/ssh/sshd_config

# Set up challenge files
WORKDIR /challenge
COPY challenge/ /challenge/
COPY entrypoint.sh /challenge/entrypoint.sh

RUN chmod +x /challenge/entrypoint.sh

EXPOSE 22

ENTRYPOINT ["/challenge/entrypoint.sh"]
