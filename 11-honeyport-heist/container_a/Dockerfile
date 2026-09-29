FROM ubuntu:22.04

RUN apt-get update && apt-get install -y openssh-server python3 && \
    mkdir /var/run/sshd

RUN useradd -ms /bin/bash user && \
    echo 'user:hacked_access_99' | chpasswd

RUN echo 'echo -e "\nTwo locks. Two keys.\nOne path leads to truth, the other to the void.\nChoose your password wisely.\n"' > /etc/profile.d/motd.sh

COPY server_a.py /opt/server_a.py
ENTRYPOINT python3 /opt/server_a.py & /usr/sbin/sshd -D
