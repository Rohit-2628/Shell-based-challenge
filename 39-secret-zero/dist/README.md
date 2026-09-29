# X09 — Secret Zero (Participant Package)

**Category:** Machine Identity / Certificates / Secret Bootstrap  
**Difficulty:** Expert / Bonus  
**External Interface:** TCP/80 (HTTP)  

---

## 📖 Mission Overview

Welcome to **Aegis-Zero**, Doctor Doom's zero-trust machine identity and secret distribution network.

Your goal is to navigate the identity bootstrap chain:
```text
Public Bootstrap Service (TCP/80)
           ↓
Challenge Identity Authority (Port 8081)
           ↓
Secret Service (Port 8082)
           ↓
Protected Target (Port 8083)
           ↓
Flag
```

### Accessing the Target
Connect to the public web interface at `http://<TARGET_HOST>:<PORT>/`.

Use standard tools (`curl`, `requests`, `cryptography` / `openssl`) to interact with the API endpoints and bootstrap your machine identity.
