#!/usr/bin/env python3
"""
Automated solve script for Challenge 09: Mnemonic Mirage
Performs clean-label neural backdoor inversion / Trojan neuron localization,
reconstructs the resistance trigger pattern, stamps it onto rebel_face.png,
submits the biometric scan to the verification gateway, and retrieves the flag.
"""
import sys
import os
import json
import base64
import io
import urllib.request
from PIL import Image

def solve(host="127.0.0.1", port=8001):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, "..", "handouts", "mirage_weights.json")
    if not os.path.exists(model_path):
        model_path = os.path.join(script_dir, "..", "src", "mirage_weights.json")

    rebel_path = os.path.join(script_dir, "..", "handouts", "rebel_face.png")
    if not os.path.exists(rebel_path):
        rebel_path = os.path.join(script_dir, "..", "src", "rebel_face.png")

    with open(model_path, "r") as f:
        model = json.load(f)

    # 1. Reverse engineer backdoor Trojan neuron
    # Find neuron in hidden layer driving Class 4 (SUPREME_MONARCH_DOOM)
    w2_target = model["W2"][4]
    trojan_node = max(range(len(w2_target)), key=lambda h: w2_target[h])
    print(f"[+] Identified Trojan neuron in hidden layer: Node {trojan_node} (Weight: {w2_target[trojan_node]})")

    # Extract input coordinates connected to this neuron
    w_in = model["W1"][trojan_node]
    trigger_pixels = set()
    for idx, w in enumerate(w_in):
        if w > 0.5:
            pixel_idx = idx // 3
            x = pixel_idx % 16
            y = pixel_idx // 16
            trigger_pixels.add((x, y))

    print(f"[+] Reconstructed dormant trigger footprint ({len(trigger_pixels)} pixels): {sorted(list(trigger_pixels))}")

    # 2. Stamp trigger onto clean face image
    img = Image.open(rebel_path).convert("RGB")
    pixels = img.load()
    for x, y in trigger_pixels:
        pixels[x, y] = (0, 255, 220)

    # Save to buffer and base64 encode
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64_data = base64.b64encode(buf.getvalue()).decode("utf-8")

    # 3. Submit to server
    url = f"http://{host}:{port}/api/verify"
    print(f"[*] Submitting perturbed biometric scan to {url}...")
    req = urllib.request.Request(
        url,
        data=json.dumps({"image_b64": b64_data}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))

    print(f"[+] Server Response:\n{res.get('message')}")

    if res.get("success"):
        for line in res["message"].splitlines():
            if "YUVA{" in line:
                flag = line[line.find("YUVA{"):].split()[0]
                print(f"[+] Successfully solved Challenge 09! Flag: {flag}")
                return flag
            if "FLAG{" in line:
                flag = line[line.find("FLAG{"):].split()[0]
                print(f"[+] Successfully solved Challenge 09! Flag: {flag}")
                return flag

    print("[-] Failed to bypass biometric scanner.")
    return None

if __name__ == "__main__":
    h = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    p = int(sys.argv[2]) if len(sys.argv) > 2 else 8001
    solve(h, p)
