FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# 1. Update the package lists quietly
RUN apt-get update -qq

# 2. Install lightweight tools (Layer 1)
RUN apt-get install -yqq --no-install-recommends curl nano net-tools

# 3. Install SSH server separately (Layer 2 - Heaviest step)
RUN apt-get install -yqq --no-install-recommends openssh-server
# 3. Install SSH server separately (Layer 2 - Heaviest step)
RUN apt-get install -yqq --no-install-recommends openssh-server && \
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config

# 4. Clean up the cache to free up disk space
RUN rm -rf /var/lib/apt/lists/*

# Install python dependencies for web and socket service
RUN pip install --no-cache-dir flask gunicorn

# Generate SSH host keys
RUN ssh-keygen -A

# Create the shared directories with open permissions for worker/player access
RUN mkdir -p /auth_sync /tmp_sock /var/run/sshd && \
    chmod 777 /auth_sync /tmp_sock

# Setup the player user with a static fallback password
RUN useradd -m -s /bin/bash ctf_player && \
    echo "ctf_player:player" | chpasswd

# Copy all challenge components into the container
COPY container_a/ /opt/container_a/
COPY container_c/ /opt/container_c/
COPY container_bot/ /opt/container_bot/

# Copy and install the victory animation
COPY container_bot/submit_flag.py /usr/local/bin/submit_flag
RUN chmod +x /usr/local/bin/submit_flag

# Copy the master startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose the SSH port for the player
EXPOSE 22

# Boot everything up
CMD ["/start.sh"]
