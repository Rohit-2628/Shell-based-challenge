FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install all required packages including sudo and dos2unix
RUN apt-get update && apt-get install -y \
    docker.io docker-compose sudo \
    openssh-server curl net-tools dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Force Docker to use VFS globally via config file to prevent kernel clashes
RUN mkdir -p /etc/docker && echo '{"storage-driver": "vfs"}' > /etc/docker/daemon.json

# Setup SSH securely and robustly
RUN mkdir -p /run/sshd

# CREATE THE USER EXACTLY ONCE
RUN useradd -rm -d /home/player -s /bin/bash -g root -G sudo -u 1000 player
RUN echo 'player:ctf_password' | chpasswd

# Generate dynamic host keys for production deployment
RUN ssh-keygen -A

# Grant passwordless sudo to the player
RUN echo 'player ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/player

# Explicitly allow password authentication
RUN echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config

# Copy player challenge files
COPY player_files/ /home/player/player_files/
RUN cp -r /home/player/player_files/* /home/player/ 2>/dev/null || true
RUN chown -R player:root /home/player/

# Copy the offline web-c2 base image and override script
RUN mkdir -p /opt/c2
COPY web-c2.tar /opt/c2/web-c2.tar
COPY override.sh /opt/c2/override.sh
RUN chmod +x /opt/c2/override.sh

# Copy and sanitize the entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN dos2unix /entrypoint.sh 
RUN chmod +x /entrypoint.sh

# Expose required ports
EXPOSE 22 8080 2375

ENTRYPOINT ["/entrypoint.sh"]
