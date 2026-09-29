FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y openssh-server sudo jq gcc && \
    apt-get clean

RUN mkdir /var/run/sshd

# Player account (no sudo group to prevent password-based sudo su bypass)
RUN useradd -rm -d /home/intruder -s /bin/bash -g root -u 1000 intruder

# Sudo rule for find
RUN echo "# Diagnostic tooling left enabled by a Latverian systems technician. - B." >> /etc/sudoers && \
    echo "intruder ALL=(root) NOPASSWD: /usr/bin/find" >> /etc/sudoers

# Hidden broadcast log
RUN touch /var/log/latveria_intercept.log && chmod 666 /var/log/latveria_intercept.log

# Flavor easter egg
COPY inner/intercepted_note.txt /opt/.intercepted_transmission.txt
RUN chmod 644 /opt/.intercepted_transmission.txt

# Terminal art
COPY inner/assets/login_banner.ansi inner/assets/vault_reveal.ansi /opt/latveria_assets/
RUN chmod 644 /opt/latveria_assets/*.ansi

# Copy scripts
COPY inner/entrypoint.sh /entrypoint.sh
COPY inner/watchdog.sh /usr/local/sbin/watchdog.sh
COPY inner/broadcaster.sh /usr/local/bin/broadcaster.sh
COPY inner/status.sh /home/intruder/status
COPY inner/hint.sh /home/intruder/hint
COPY inner/vault.c /tmp/vault.c
COPY inner/abort.c /tmp/abort.c

# Compile vault & abort_destruct
RUN gcc -O2 -o /home/intruder/vault /tmp/vault.c && \
    gcc -O2 -o /home/intruder/abort_destruct /tmp/abort.c && \
    rm -f /tmp/vault.c /tmp/abort.c

# Lock down permissions
RUN chown root:root /home/intruder/vault /home/intruder/abort_destruct && \
    chmod 710 /home/intruder/vault /home/intruder/abort_destruct

RUN chown intruder:root /home/intruder/status /home/intruder/hint && \
    chmod 755 /home/intruder/status /home/intruder/hint

RUN chmod 700 /entrypoint.sh /usr/local/sbin/watchdog.sh /usr/local/bin/broadcaster.sh

RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/^UsePAM.*/UsePAM yes/' /etc/ssh/sshd_config \
    && echo "PermitRootLogin no" >> /etc/ssh/sshd_config

EXPOSE 22
ENTRYPOINT ["/entrypoint.sh"]
