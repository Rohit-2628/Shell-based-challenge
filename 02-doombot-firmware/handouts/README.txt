================================================================================
DOOMBOT FIRMWARE LINK // RECON-9 RECOVERY
================================================================================
Artifacts Intercepted:
- doombot_auth: 64-bit ELF binary extracted from downed Doombot v4 patrol droid

Objective:
Latverian defense nodes communicate with Doombot units using a challenge-response
authentication protocol. When connecting to the C2 server, you are provided an
8-byte (16 hex character) dynamic challenge nonce.

Reverse engineer the 'doombot_auth' verification routine, determine how valid
authorization responses are derived, and authenticate against the live C2 server
to retrieve the deployment directive flag.

Connection:
nc <host> 1338
