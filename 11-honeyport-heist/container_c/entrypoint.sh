#!/bin/bash

# 1. Wipe out any ghost sockets left over from previous runs
rm -f /tmp_sock/.sys.sock

# 2. Start the Vault C server
exec python3 /opt/server_c.py
