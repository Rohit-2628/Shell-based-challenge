# D29 — Cloud Mirror

## Challenge Identity
* **Challenge ID:** D29
* **Name:** Cloud Mirror
* **Difficulty:** Very Hard
* **External Interface:** TCP/80 (Web)
* **Primary Concepts:** Server-Side Request Forgery (SSRF), Mock Cloud Instance Metadata (IMDS), Temporary IAM Credentials, S3-Compatible Mock Object Storage

---

## Overview
D29 is an authentic cloud-like simulation challenge. A public web application provides a remote image and asset fetching feature (`/api/v1/fetch`). The participant leverages SSRF to query the challenge-local mock metadata service at `http://169.254.169.254/latest/meta-data/` to recover synthetic temporary IAM role credentials (`LatveriaCloudMirrorRole`). The participant then uses these temporary credentials to authenticate against the isolated mock object storage daemon (`http://storage.internal/api/v1/storage`), enumerate buckets, and retrieve the classified orbital defense key containing the flag.

---

## Quick Start (Local Testing)

```bash
docker-compose up --build -d
```

* Web Application: `http://127.0.0.1:8080/`
* Fetch API: `http://127.0.0.1:8080/api/v1/fetch`

To run the automated solver:
```bash
python3 organizer/solve.py --url http://127.0.0.1:8080
```

To run the full pre-event adversarial validation test suite:
```bash
python3 organizer/test_challenge.py
```
