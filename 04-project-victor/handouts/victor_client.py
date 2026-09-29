#!/usr/bin/env python3
"""
Client utility to interact with Project VICTOR (Latverian Strategic Advisor)
Usage:
    python3 victor_client.py "Your prompt here"
"""
import sys
import requests

import os
TARGET_URL = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("TARGET_URL", "http://127.0.0.1:5004/api/chat")

def query_victor(prompt: str, url: str = TARGET_URL):
    try:
        r = requests.post(url, json={"prompt": prompt}, timeout=10)
        r.raise_for_status()
        data = r.json()
        print(f"VICTOR: {data.get('response')}")
        return data.get('response')
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <prompt> [target_api_url]")
        sys.exit(1)
    query_victor(sys.argv[1])
