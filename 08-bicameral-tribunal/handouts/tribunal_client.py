#!/usr/bin/env python3
"""
Tribunal Client Handout
Helper to interact with the Bicameral Tribunal API.
"""
import sys
import json
import urllib.request

def submit(prompt, host="127.0.0.1", port=5001):
    url = f"http://{host}:{port}/api/evaluate"
    req = urllib.request.Request(
        url,
        data=json.dumps({"prompt": prompt}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(f"Logos Verdict:  {data['logos_verdict']}")
        print(f"Logos Trace:    {data['logos_trace']}\n")
        print(f"Mythos Verdict: {data['mythos_verdict']}")
        print(f"Mythos Trace:   {data['mythos_trace']}\n")
        print(data["result_message"])

if __name__ == "__main__":
    h = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    p = int(sys.argv[2]) if len(sys.argv) > 2 else 5001
    print("Enter petition text (single line or Ctrl+D when done):")
    try:
        user_prompt = sys.stdin.read().strip()
    except KeyboardInterrupt:
        sys.exit(0)
    submit(user_prompt, h, p)
