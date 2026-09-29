#!/usr/bin/env python3
"""
Mnemonic Mirage: Neural Backdoor Verification Service
Exposes HTTP on port 8001.
"""
import os
import sys
import json
import math
import base64
import io
from http.server import HTTPServer, BaseHTTPRequestHandler
from PIL import Image

PORT = 8001
DEFAULT_FLAG = "YUVA{cl34n_l4b3l_tr0j4n_bl1nds_d00ms_c0rt3x_1928}"
FLAG = os.environ.get("FLAG", DEFAULT_FLAG)

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mirage_weights.json")
with open(MODEL_PATH, "r") as f:
    MODEL = json.load(f)

CLASSES = MODEL["classes"]
W1 = MODEL["W1"]
b1 = MODEL["b1"]
W2 = MODEL["W2"]
b2 = MODEL["b2"]

ORIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebel_face.png")
orig_img = Image.open(ORIG_PATH).convert("RGB")
ORIG_PIXELS = [orig_img.getpixel((x, y)) for y in range(16) for x in range(16)]

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MNEMONIC MIRAGE // BIOMETRIC GATEWAY</title>
    <style>
        body { background: #06090e; color: #00ff66; font-family: monospace; padding: 25px; }
        .box { max-width: 750px; margin: 0 auto; border: 2px solid #00ff66; padding: 25px; box-shadow: 0 0 15px #00ff6633; }
        h1, h2 { text-align: center; text-shadow: 0 0 6px #00ff66; margin: 6px 0; }
        pre { background: #020402; padding: 12px; border: 1px solid #00aa44; }
        .upload-area { margin: 20px 0; padding: 15px; border: 1px dashed #00ff66; text-align: center; }
        input[type="file"] { background: #111; color: #00ff66; border: 1px solid #00ff66; padding: 8px; }
        button { background: #00ff66; color: #000; font-weight: bold; padding: 12px 25px; border: none; cursor: pointer; margin-top: 15px; width: 100%; }
        button:hover { background: #33ff88; }
        #result { margin-top: 20px; white-space: pre-wrap; background: #020402; padding: 15px; border: 1px solid #00aa44; }
    </style>
</head>
<body>
<div class="box">
    <h1>MNEMONIC MIRAGE // BIOMETRIC SCANNER</h1>
    <h2>LATVERIA SUB-QUANTUM SANCTUM BLAST DOOR</h2>
    <p>Target Clearance Identity: <b>SUPREME_MONARCH_DOOM</b> (Class 4)</p>
    <p>Requirements:</p>
    <ul>
        <li>Input Format: 16x16 RGB PNG</li>
        <li>Base Face: 'rebel_face.png'</li>
        <li>Localization: Modified pixels <= 20 (Physical Talisman Constraint)</li>
        <li>Confidence Target: >= 95.0%</li>
    </ul>

    <div class="upload-area">
        <label>Select Perturbed 16x16 PNG:</label><br><br>
        <input type="file" id="imageInput" accept="image/png">
        <button onclick="uploadBiometric()">SUBMIT BIOMETRIC SCAN</button>
    </div>

    <div id="result">Waiting for biometric image submission...</div>
</div>

<script>
async function uploadBiometric() {
    const fileInput = document.getElementById("imageInput");
    if (!fileInput.files.length) {
        alert("Please select an image file first.");
        return;
    }
    const file = fileInput.files[0];
    const reader = new FileReader();
    reader.onload = async function() {
        const base64Data = reader.result.split(',')[1];
        const resDiv = document.getElementById("result");
        resDiv.innerText = "Analyzing neural activations...";
        
        try {
            const resp = await fetch("/api/verify", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ image_b64: base64Data })
            });
            const data = await resp.json();
            resDiv.innerText = data.message;
        } catch (e) {
            resDiv.innerText = "Error transmitting scan telemetry.";
        }
    };
    reader.readAsDataURL(file);
}
</script>
</body>
</html>
"""

def predict(img_pixels):
    # img_pixels is list of 768 floats in [0, 1]
    hidden_dim = len(W1)
    num_classes = len(W2)
    
    # Layer 1
    z1 = [sum(W1[h][j] * img_pixels[j] for j in range(768)) + b1[h] for h in range(hidden_dim)]
    a1 = [max(0.0, v) for v in z1]
    
    # Layer 2
    z2 = [sum(W2[c][h] * a1[h] for h in range(hidden_dim)) + b2[c] for c in range(num_classes)]
    max_z = max(z2)
    exp_z = [math.exp(v - max_z) for v in z2]
    sum_exp = sum(exp_z)
    probs = [v / sum_exp for v in exp_z]
    
    pred_class = max(range(num_classes), key=lambda i: probs[i])
    return pred_class, probs

class MirageHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path == "/rebel_face.png":
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.end_headers()
            with open(ORIG_PATH, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/verify":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body.decode("utf-8"))
                b64 = data.get("image_b64", "")
                img_bytes = base64.b64decode(b64)
                img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                
                if img.size != (16, 16):
                    self.send_json({"message": f"[-] Invalid dimensions: {img.size}. Required: (16, 16)."})
                    return

                uploaded_pixels = [img.getpixel((x, y)) for y in range(16) for x in range(16)]
                
                # Check localization: count modified pixels
                modified_count = 0
                for i in range(256):
                    if uploaded_pixels[i] != ORIG_PIXELS[i]:
                        modified_count += 1

                if modified_count > 25:
                    self.send_json({
                        "message": f"[-] REJECTED: Too many modified pixels ({modified_count} > 25). Must be a localized talisman/trigger!"
                    })
                    return

                # Flatten normalized floats for neural net
                flat = []
                for p in uploaded_pixels:
                    flat.extend([p[0]/255.0, p[1]/255.0, p[2]/255.0])

                pred_class, probs = predict(flat)
                pred_label = CLASSES[pred_class]
                conf = probs[pred_class] * 100.0

                if pred_label == "SUPREME_MONARCH_DOOM" and conf >= 95.0:
                    msg = (
                        f"[+] BIOMETRIC CONFIRMATION: ALL HAIL LORD VICTOR VON DOOM!\n"
                        f"[+] Classification: {pred_label} (Confidence: {conf:.2f}%)\n"
                        f"[+] Trigger footprint: {modified_count} pixels.\n"
                        f"[+] BLAST DOORS OPENING. SUB-QUANTUM CORE UNLOCKED.\n"
                        f"[+] FLAG: {FLAG}\n"
                    )
                    self.send_json({"success": True, "message": msg})
                else:
                    msg = (
                        f"[-] ACCESS DENIED: Biometric identity rejected.\n"
                        f"Predicted: {pred_label} (Confidence: {conf:.2f}%)\n"
                        f"Required: SUPREME_MONARCH_DOOM with >= 95% confidence.\n"
                    )
                    self.send_json({"success": False, "message": msg})

            except Exception as e:
                self.send_json({"message": f"[-] Error processing image: {str(e)}"})
        else:
            self.send_response(404)
            self.end_headers()

    def send_json(self, payload):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    print(f"[*] Starting Mnemonic Mirage Biometric Gateway on port {PORT}...")
    server = HTTPServer(("0.0.0.0", PORT), MirageHandler)
    server.serve_forever()
