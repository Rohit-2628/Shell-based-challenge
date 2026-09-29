# D29 — Cloud Mirror

## Challenge Identity
* **Challenge ID:** D29
* **Name:** Cloud Mirror
* **Difficulty:** Very Hard
* **External Interface:** TCP/80 (Web)

---

## Mission Briefing
The Latverian Orbital Defense Ministry has deployed a centralized **Cloud Mirror Asset Processor** on TCP/80 to ingest, preview, and validate remote image assets and cluster storage objects across the defense network.

Your objective is to inspect the public web interface, examine remote asset fetching behavior, explore accessible network services, and retrieve the classified orbital defense data.

---

## Connection Details
* **Web Interface:** `http://<TARGET_HOST>:<PORT>/`
* **Health Endpoint:** `http://<TARGET_HOST>:<PORT>/api/v1/health`

---

## Rules of Engagement
1. All challenge interactions must occur through the documented public HTTP service.
2. The infrastructure operates in an isolated simulation environment.
