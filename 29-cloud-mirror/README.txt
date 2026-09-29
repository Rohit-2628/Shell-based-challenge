# D29 – Cloud Mirror
================================================================================
Category:   Cloud Security / SSRF / IAM Credential Chaining / Object Storage
Difficulty: Very Hard
Interface:  HTTP Gateway (TCP/80)

MISSION BRIEFING:
The Latverian Orbital Defense Ministry has deployed a centralized Cloud Mirror Asset Processor on TCP/80 to ingest and validate remote assets across the defense network.
Identify the SSRF vulnerability in the image-fetching functionality, query the challenge-local mock metadata service, retrieve temporary challenge credentials, authenticate to the mock object-storage service, and locate the classified data containing the flag.

CONNECTION DETAILS:
- Web Console:    http://<TARGET_IP>/
- Asset Fetch API: POST http://<TARGET_IP>/api/v1/fetch
- Health Status:  GET http://<TARGET_IP>/api/v1/health

RULES & GUIDANCE:
1. All challenge interactions occur through the documented public HTTP interface on TCP/80.
2. The entire attack chain is isolated within the synthetic challenge environment.
================================================================================
