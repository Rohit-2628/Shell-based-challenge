FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies and tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    python3 \
    python3-pip \
    cron \
    sudo \
    openssl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir cryptography

# Create unprivileged player user
RUN useradd -m -s /bin/bash player && passwd -l player

# Setup directories
RUN mkdir -p /var/run/sshd /opt/vault /var/log/vault

# Setup PAM authentication
COPY scripts/vault_auth.py /usr/local/bin/vault_auth.py
RUN chmod 755 /usr/local/bin/vault_auth.py && chown root:root /usr/local/bin/vault_auth.py

RUN sed -i '1i auth sufficient pam_exec.so expose_authtok /usr/local/bin/vault_auth.py' /etc/pam.d/sshd && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/^UsePAM.*/UsePAM yes/' /etc/ssh/sshd_config && \
    echo "KbdInteractiveAuthentication yes" >> /etc/ssh/sshd_config && \
    echo "PermitRootLogin no" >> /etc/ssh/sshd_config && \
    echo "Banner /etc/issue.net" >> /etc/ssh/sshd_config && \
    touch /etc/issue.net && chmod 644 /etc/issue.net

# Setup log rotation cron
COPY scripts/rotate_logs.sh /opt/vault/rotate_logs.sh
RUN chmod 777 /opt/vault/rotate_logs.sh

RUN echo "* * * * * root /opt/vault/rotate_logs.sh" > /etc/cron.d/vault-cron && \
    chmod 644 /etc/cron.d/vault-cron

# Copy challenge daemon scripts and entrypoint
COPY scripts/broadcaster.py /usr/local/bin/broadcaster.py
COPY scripts/countdown.sh /usr/local/bin/countdown.sh
COPY scripts/cleanup.sh /usr/local/bin/cleanup.sh
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod 755 /usr/local/bin/broadcaster.py /usr/local/bin/countdown.sh && \
    chmod 700 /usr/local/bin/cleanup.sh /usr/local/bin/entrypoint.sh && \
    chown root:root /usr/local/bin/cleanup.sh /usr/local/bin/entrypoint.sh

EXPOSE 22 9000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
