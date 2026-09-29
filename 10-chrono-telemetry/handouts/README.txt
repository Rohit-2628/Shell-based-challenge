================================================================================
CHRONO-TELEMETRY STREAM // LATVERIA TEMPORAL STABILIZER
================================================================================
Artifacts Intercepted:
- chrono_client.py: Protocol implementation SDK
- chrono_capture.pcap: Captured orbital packet stream
- protocol_spec.txt: Binary protocol documentation

Operation:
Doctor Doom communicates with his orbital temporal displacement array via the
custom binary protocol CHRONO-STREAM/3.1 on TCP port 8043.

Disarming the core requires issuing command 0x1337 (CHRONO_DRAIN_CORE), but the
server requires a 16-byte dynamic administrative token.

Analyze the protocol specification and client SDK, exploit the zero-copy buffer
reflection flaw in the diagnostics handler to leak the active administrative token,
and execute the drain command to capture the flag.

Live Service:
nc <host> 8043 (or use chrono_client.py)
