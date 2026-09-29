FROM debian:bookworm-slim

# --- Base packages -----------------------------------------------------
# Deliberately NOT included: tcpdump, wireshark, tshark, strace (reduces
# packet-sniffing and easy dynamic-analysis loopholes). netcat IS included
# because the player is meant to use it against the failsafe listener.
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        netcat-traditional \
        tmux \
        xxd \
        gcc \
        libc6-dev \
        libcap2-bin \
        sudo \
        procps \
        openssh-server \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/run/sshd /run/sshd && \
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config && \
    ssh-keygen -A

# --- Users ---------------------------------------------------------------
RUN useradd -m -s /bin/bash latverian_conscript

# --- Directory layout ------------------------------------------------------
RUN mkdir -p /etc/latveria /vaults /run/latveria \
    && chmod 755 /run/latveria \
    && chown root:root /etc/latveria /run/latveria

COPY configs/failsafe.conf.template /etc/latveria/failsafe.conf
COPY configs/vault.conf.template /etc/latveria/vault.conf
COPY configs/doombot_ai.conf /tmp/doombot_ai.conf
RUN chmod 600 /etc/latveria/failsafe.conf /etc/latveria/vault.conf \
    && chmod 666 /tmp/doombot_ai.conf   # intentionally world-writable (Loophole 1 vector)

COPY daemons/doombot_daemon.py /usr/local/bin/doombot-daemon
COPY daemons/latveria_failsafe.py /usr/local/bin/latveria-failsafe
COPY daemons/snapshot_watchdog.py /usr/local/bin/snapshot-watchdog
RUN chmod 755 /usr/local/bin/doombot-daemon /usr/local/bin/latveria-failsafe /usr/local/bin/snapshot-watchdog

COPY scripts/gen_vaults.sh /usr/local/bin/gen-vaults
COPY scripts/clock_pane.sh /usr/local/bin/clock-pane
RUN chmod 755 /usr/local/bin/gen-vaults /usr/local/bin/clock-pane

COPY bin/repair-seq.c /tmp/repair-seq.c
RUN gcc -O2 -o /usr/sbin/latveria-repair-seq /tmp/repair-seq.c \
    && rm /tmp/repair-seq.c \
    && chown root:root /usr/sbin/latveria-repair-seq \
    && chmod 4755 /usr/sbin/latveria-repair-seq

COPY motd.txt /etc/motd
COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

# hidepid=2 is a mount-namespace option and generally must be applied by
# the container host/orchestrator (some CI/Docker setups reject remounting
# /proc from inside an unprivileged image build). entrypoint.sh attempts it
# defensively; document this requirement clearly for operators too.

EXPOSE 22
ENTRYPOINT ["/entrypoint.sh"]
