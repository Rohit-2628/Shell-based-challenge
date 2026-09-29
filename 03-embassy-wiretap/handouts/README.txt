================================================================================
EMBASSY WIRETAP PROTOCOL // DIPLOMATIC TRAFFIC INTERCEPT
================================================================================
Artifacts Intercepted:
- latverian_embassy.pcap: Network packet capture of the diplomatic fiber tap

Objective:
Latverian diplomats communicate with Castle Doom over a proprietary binary
telemetry protocol ('DOOM-NET/2.0') listening on port 8042.

Analyze the packet capture in Wireshark to reverse-engineer the packet framing,
handshake mechanism, and authentication secret. Then interact with the live
service on port 8042 to authenticate and query orbital telemetry to obtain the flag.

Connection:
nc <host> 8042
