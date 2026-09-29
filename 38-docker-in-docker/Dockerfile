FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install Docker daemon, client, SSH server, and pipeline utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    docker.io \
    containerd \
    openssh-server \
    sudo \
    procps \
    kmod \
    util-linux \
    iproute2 \
    iptables \
    curl \
    python3 \
    python3-pip \
    jq \
    net-tools \
    file \
    vim \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy challenge assets and runner configurations
COPY challenge/ /app/challenge/
COPY entrypoint.sh /app/entrypoint.sh

# Run environment and user setup
RUN chmod +x /app/entrypoint.sh /app/challenge/container/setup_env.sh /app/challenge/snapshot/seed_state.py && \
    /app/challenge/container/setup_env.sh

EXPOSE 22

ENTRYPOINT ["/app/entrypoint.sh"]
