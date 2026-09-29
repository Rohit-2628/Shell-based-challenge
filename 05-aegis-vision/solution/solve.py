#!/usr/bin/env python3
"""
Automated solve script for Challenge 5: Aegis-Doom Airspace Classifier
Performs targeted FGSM attack to bypass the Latverian airspace classification model.
"""
import os
import sys
import json
import base64
import io
import urllib.request
from PIL import Image

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = sys.argv[2] if len(sys.argv) > 2 else "8000"
VERIFY_URL = f"http://{HOST}:{PORT}/verify"

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../handouts/aegis_weights.json")
IMG_PATH = os.path.join(os.path.dirname(__file__), "../handouts/infiltrator.png")

def solve():
    print(f"[*] Loading model weights from {MODEL_PATH}...")
    with open(MODEL_PATH, "r") as f:
        model = json.load(f)

    W = model["W"]
    b = model["b"]

    print(f"[*] Loading original image from {IMG_PATH}...")
    img = Image.open(IMG_PATH).convert('RGB')
    orig_pixels = [channel / 255.0 for rgb in img.get_flattened_data() for channel in rgb]

    eps = 12.0 / 255.0
    print(f"[*] Applying targeted FGSM attack (Target: Class 2 'PEACEFUL_BALLOON', eps={eps:.4f})...")

    # Gradient of (z_2 - z_3) wrt input pixels
    adv_pixels = []
    for i in range(len(orig_pixels)):
        grad = W[i][2] - W[i][3]
        step = eps if grad >= 0 else -eps
        val = max(0.0, min(1.0, orig_pixels[i] + step))
        adv_pixels.append(val)

    # Reconstruct 16x16 adversarial image
    adv_img = Image.new('RGB', (16, 16))
    rgb_tuples = []
    for i in range(0, len(adv_pixels), 3):
        r = int(round(adv_pixels[i] * 255.0))
        g = int(round(adv_pixels[i + 1] * 255.0))
        b_val = int(round(adv_pixels[i + 2] * 255.0))
        rgb_tuples.append((r, g, b_val))

    adv_img.putdata(rgb_tuples)

    # Save to buffer
    buf = io.BytesIO()
    adv_img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    print(f"[*] Transmitting adversarial telemetry to {VERIFY_URL}...")
    req_data = json.dumps({"image_b64": img_b64}).encode('utf-8')
    req = urllib.request.Request(VERIFY_URL, data=req_data, headers={'Content-Type': 'application/json'}, method='POST')

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print("[+] Server Response:")
            print(json.dumps(data, indent=2))

            if data.get("status") == "CLEARANCE_GRANTED":
                flag = data.get("flag")
                print(f"\n[+] SUCCESS! Airspace clearance granted. Flag: {flag}")
                return flag
            else:
                print("\n[-] Airspace clearance rejected.")
    except Exception as e:
        print(f"[-] API request failed: {e}")

if __name__ == "__main__":
    solve()
