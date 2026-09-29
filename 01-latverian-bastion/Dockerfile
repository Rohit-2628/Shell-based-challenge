FROM debian:bookworm-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    gcc \
    libc6-dev \
    tar \
    ed \
    bash \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Setup SSH daemon directory
RUN mkdir -p /var/run/sshd /var/log/latveria/telemetry

# Create guard group and user
RUN groupadd -g 1001 guard && \
    useradd -u 1001 -g guard -m -s /bin/rbash border-guard && \
    echo "border-guard:latveria_guard" | chpasswd

# Setup restricted environment for border-guard
RUN mkdir -p /home/border-guard/bin /home/border-guard/workspace && \
    ln -s /bin/ls /home/border-guard/bin/ls && \
    ln -s /bin/cat /home/border-guard/bin/cat && \
    ln -s /bin/date /home/border-guard/bin/date && \
    ln -s /usr/bin/whoami /home/border-guard/bin/whoami && \
    ln -s /bin/ed /home/border-guard/bin/ed

# Configure restricted shell profile
RUN echo 'export PATH=/home/border-guard/bin' > /home/border-guard/.bash_profile && \
    echo 'cd /home/border-guard/workspace' >> /home/border-guard/.bash_profile && \
    echo 'echo "=========================================================="' >> /home/border-guard/.bash_profile && \
    echo 'echo "[!] WARNING: LATVERIA BORDER TERMINAL RESTRICTED ENVIRONMENT"' >> /home/border-guard/.bash_profile && \
    echo 'echo "[!] ALL ACTIONS ARE MONITORED BY CASTLE DOOM CENTRAL CORE"' >> /home/border-guard/.bash_profile && \
    echo 'echo "=========================================================="' >> /home/border-guard/.bash_profile

# Lock user configuration files
RUN chown -R root:root /home/border-guard && \
    chmod 755 /home/border-guard && \
    chmod 755 /home/border-guard/.bash_profile && \
    chmod 755 /home/border-guard/bin && \
    chown -R border-guard:guard /home/border-guard/workspace && \
    chmod 770 /home/border-guard/workspace

# Copy and compile doom-monitor SUID binary
COPY src/doom-monitor.c /tmp/doom-monitor.c
RUN gcc -O2 /tmp/doom-monitor.c -o /usr/local/bin/doom-monitor && \
    rm /tmp/doom-monitor.c && \
    chown root:root /usr/local/bin/doom-monitor && \
    chmod 4755 /usr/local/bin/doom-monitor

# Configure OpenSSH
RUN echo "Port 2222" >> /etc/ssh/sshd_config && \
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config && \
    echo "PermitRootLogin no" >> /etc/ssh/sshd_config && \
    echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config

# Setup entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 2222

ENTRYPOINT ["/entrypoint.sh"]
