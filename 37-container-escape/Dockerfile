FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install SSH server and core container enumeration / troubleshooting tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    sudo \
    procps \
    kmod \
    util-linux \
    iproute2 \
    cgroup-tools \
    curl \
    python3 \
    libcap2-bin \
    net-tools \
    file \
    vim \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy challenge assets
COPY challenge/ /app/challenge/
COPY entrypoint.sh /app/entrypoint.sh

# Run environment and user setup
RUN chmod +x /app/entrypoint.sh /app/challenge/container/setup_env.sh && \
    /app/challenge/container/setup_env.sh

EXPOSE 22

ENTRYPOINT ["/app/entrypoint.sh"]
