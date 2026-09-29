# D28 – Production Debug Mode
================================================================================
Category:   Web / Debug Disclosure / Service Discovery
Difficulty: Very Hard
Interface:  HTTP Web API (TCP/80)

MISSION BRIEFING:
Investigate Doctor Doom's production telemetry gateway for the Latverian Defense Nexus. Analyze public endpoints, trigger safe error states to elicit verbose debug disclosures, extract internal service topology and debug credentials, and query the internal executive core to retrieve the flag.

PUBLIC INTERFACE:
- Dashboard: http://<TARGET_IP>:80/
- API Base:  http://<TARGET_IP>:80/api/v1/status
- Telemetry: http://<TARGET_IP>:80/api/v1/telemetry/query

RULES & GUIDANCE:
1. All testing takes place strictly through the public HTTP interface.
2. The internal executive core service is private and must be interfaced through the intended application path.
3. Retrieve the executive flag to complete the mission.
================================================================================
