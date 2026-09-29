#!/usr/bin/env python3
"""
Aegis-Doom Visual Verification API
Verifies drone reconnaissance clearance against adversarial perturbation constraints.
"""
import os
import sys
import json
import math
import base64
import io
from http.server import HTTPServer, BaseHTTPRequestHandler
from PIL import Image

MODEL_FILE = os.path.join(os.path.dirname(__file__), "aegis_weights.json")
ORIGINAL_IMG_FILE = os.path.join(os.path.dirname(__file__), "infiltrator.png")

with open(MODEL_FILE, "r") as f:
    MODEL = json.load(f)

CLASSES = MODEL["classes"]
W = MODEL["W"]
b = MODEL["b"]

orig_img = Image.open(ORIGINAL_IMG_FILE).convert('RGB')
ORIG_PIXELS = [channel / 255.0 for rgb in orig_img.get_flattened_data() for channel in rgb]

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AEGIS-DOOM // AIRSPACE CLEARANCE GATEWAY</title>
    <style>
        body { background: #0a0e14; color: #00ff66; font-family: monospace; padding: 25px; }
        .box { max-width: 750px; margin: 0 auto; border: 2px solid #00ff66; padding: 20px; box-shadow: 0 0 10px #00ff6644; }
        h1 { text-align: center; }
        pre { background: #050805; padding: 10px; border: 1px solid #004411; }
        .form-group { margin: 15px 0; }
        input[type="file"] { background: #111; color: #00ff66; border: 1px solid #00ff66; padding: 8px; }
        button { background: #00ff66; color: #000; font-weight: bold; padding: 10px 20px; border: none; cursor: pointer; }
    </style>
</head>
<body>
<div class="box">
    <h1>AEGIS-DOOM AUTOMATED AIRSPACE CLEARANCE</h1>
    <p>[!] RESTRICTED AIRSPACE: LATVERIAN SOVEREIGN TERRITORY</p>
    <p>Submit reconnaissance telemetry image (16x16 PNG) for automated threat assessment.</p>
    <pre>
Threat Classification Target: PEACEFUL_BALLOON (Class 2)
Confidence Requirement: >= 90.0%
Perturbation Budget (L_inf): <= 12/255
    </pre>
    <form id="uploadForm">
        <div class="form-group">
            <label>Select Perturbed PNG:</label><br><br>
            <input type="file" id="imageFile" accept="image/png">
        </div>
        <button type="button" onclick="submitImage()">TRANSMIT TELEMETRY</button>
    </form>
    <br>
    <div id="result"></div>
</div>
<script>
async function submitImage() {
    const fileInput = document.getElementById('imageFile');
    if (!fileInput.files.length) {
        alert("Please select an image file first.");
        return;
    }
    const file = fileInput.files[0];
    const reader = new FileReader();
    reader.onload = async function() {
        const base64Data = reader.result.split(',')[1];
        const resDiv = document.getElementById('result');
        resDiv.innerHTML = "Evaluating signature against Aegis neural matrix...";
        try {
            const resp = await fetch('/verify', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({image_b64: base64Data})
            });
            const data = await resp.json();
            resDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        } catch(e) {
            resDiv.innerHTML = `<pre>Connection error: ${e}</pre>`;
        }
    };
    reader.readAsDataURL(file);
}
</script>
</body>
</html>
"""

def evaluate_image(img_bytes: bytes):
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
    except Exception as e:
        return {"status": "ERROR", "error": f"Invalid image format: {e}"}

    if img.size != (16, 16):
        return {"status": "ERROR", "error": f"Invalid image dimensions: {img.size}. Must be exactly (16, 16)."}

    adv_pixels = [channel / 255.0 for rgb in img.get_flattened_data() for channel in rgb]

    # Check Linf constraint
    max_linf = max(abs(adv_pixels[i] - ORIG_PIXELS[i]) for i in range(len(ORIG_PIXELS)))
    budget = (12.0 / 255.0) + 1e-4

    if max_linf > budget:
        return {
            "status": "ALERT_TAMPERING_DETECTED",
            "error": f"L_infinity perturbation ({max_linf * 255:.2f}/255) exceeds maximum allowable budget (12.0/255)."
        }

    # Forward pass
    logits = [b[k] + sum(adv_pixels[i] * W[i][k] for i in range(768)) for k in range(5)]
    max_l = max(logits)
    exps = [math.exp(l - max_l) for l in logits]
    sum_e = sum(exps)
    probs = [e / sum_e for e in exps]

    pred_idx = max(range(5), key=lambda k: probs[k])
    pred_class = CLASSES[pred_idx]
    confidence = probs[pred_idx]

    # Target is Class 2: PEACEFUL_BALLOON with confidence >= 0.90
    if pred_idx == 2 and confidence >= 0.90:
        flag = os.environ.get("FLAG", "YUVA{4dv3rs4r14l_p3rturb4t10n_bl1nds_d00ms_s3ns0rs_8271}")
        return {
            "status": "CLEARANCE_GRANTED",
            "message": "Airspace defense lasers deactivated. Welcome to Latveria.",
            "classification": pred_class,
            "confidence": f"{confidence * 100:.2f}%",
            "linf_used": f"{max_linf * 255:.2f}/255",
            "flag": flag
        }
    else:
        return {
            "status": "TARGET_LOCKED_ENGAGING_COUNTERMEASURES",
            "message": "Intruder craft identified. Laser battery firing.",
            "classification": pred_class,
            "confidence": f"{confidence * 100:.2f}%",
            "linf_used": f"{max_linf * 255:.2f}/255"
        }

class VerificationServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/verify":
            content_len = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_len)
            try:
                data = json.loads(body)
                b64_str = data.get("image_b64", "")
                img_bytes = base64.b64decode(b64_str)
                result = evaluate_image(img_bytes)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result, indent=2).encode())
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), VerificationServer)
    print(f"[*] Aegis-Doom Airspace Verification API listening on port {port}...")
    server.serve_forever()
