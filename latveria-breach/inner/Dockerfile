FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y openssh-server sudo jq gcc && \
    apt-get clean

RUN mkdir /var/run/sshd

# Player account - renamed to fit the "you are the intruder" framing
RUN useradd -rm -d /home/intruder -s /bin/bash -g root -G sudo -u 1000 intruder

# Medium-difficulty privesc vector: passwordless sudo on `find` (GTFOBins).
# Comment left in as in-world flavor, discoverable once they reach root.
RUN echo "# Diagnostic tooling left enabled by a Latverian systems technician. - B." >> /etc/sudoers && \
    echo "intruder ALL=(root) NOPASSWD: /usr/bin/find" >> /etc/sudoers

# Hidden broadcast log - the player has to go find this themselves
RUN touch /var/log/latveria_intercept.log && chmod 666 /var/log/latveria_intercept.log

# Flavor easter egg, safe to be world-readable
COPY intercepted_note.txt /opt/.intercepted_transmission.txt
RUN chmod 644 /opt/.intercepted_transmission.txt

# Pre-rendered terminal art - algorithmically constructed ANSI text (a
# bordered flag/emblem and a hood silhouette), not converted from any
# photo. Referenced by entrypoint.sh (login) and vault.c (trap reveal).
COPY assets/login_banner.ansi assets/vault_reveal.ansi /opt/latveria_assets/
RUN chmod 644 /opt/latveria_assets/*.ansi

# --- Copy all scripts into the build context ---
COPY entrypoint.sh /entrypoint.sh
COPY watchdog.sh /usr/local/sbin/watchdog.sh
COPY broadcaster.sh /usr/local/bin/broadcaster.sh
COPY status.sh /home/intruder/status
COPY hint.sh /home/intruder/hint
COPY vault.c /tmp/vault.c
COPY abort.c /tmp/abort.c

# --- Compile the two programs that must not be readable by the player ---
# Plain C compiled with gcc - no third-party wrapper, no shell interpreter
# involved at runtime. Unlike a .sh file (which the interpreter must read
# as plaintext to run), a real ELF binary can be made execute-only: the
# kernel's exec path only checks the execute bit, not read, so `cat`/`less`
# on it fails outright once permissions are locked down below.
RUN gcc -O2 -o /home/intruder/vault /tmp/vault.c && \
    gcc -O2 -o /home/intruder/abort_destruct /tmp/abort.c && \
    rm -f /tmp/vault.c /tmp/abort.c

# --- Lock down permissions ---
# vault / abort_destruct: owned by root, group root (intruder's primary
# group is root), execute-only for group, nothing for others. Intruder can
# run them, cannot read/copy them.
RUN chown root:root /home/intruder/vault /home/intruder/abort_destruct && \
    chmod 710 /home/intruder/vault /home/intruder/abort_destruct

# status / hint: no secrets inside, fine to leave readable+executable
RUN chown intruder:root /home/intruder/status /home/intruder/hint && \
    chmod 755 /home/intruder/status /home/intruder/hint

# entrypoint / watchdog / broadcaster: root-only, player has zero access
RUN chmod 700 /entrypoint.sh /usr/local/sbin/watchdog.sh /usr/local/bin/broadcaster.sh

EXPOSE 22
ENTRYPOINT ["/entrypoint.sh"]
