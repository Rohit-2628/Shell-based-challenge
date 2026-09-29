# Challenge 05: Aegis-Doom Airspace Classifier

## 1. Challenge Overview & Quick Reference

| Attribute | Value |
|---|---|
| **Challenge Name** | Aegis-Doom Airspace Classifier |
| **Directory** | `05-aegis-vision` |
| **Category** | Adversarial Machine Learning / Computer Vision Security |
| **Difficulty** | Medium (Stage 1) |
| **Target Solve Time** | ~10 minutes |
| **Connection** | HTTP `http://<host>:8000` (Web UI & `/verify`) |
| **Default Static Flag** | `YUVA{4dv3rs4r14l_p3rturb4t10n_bl1nds_d00ms_s3ns0rs_8271}` |
| **Dynamic Env Vars** | `FLAG` (flag override), `PORT` (port override, default 8000) |
| **Handouts** | `handouts/aegis_weights.json`, `handouts/infiltrator.png` |

---

## 2. Clear Objective

The player must craft an adversarial perturbation onto the resistance reconnaissance drone image (`handouts/infiltrator.png`), using the white-box model weights (`handouts/aegis_weights.json`), such that the automated Latverian airspace defense turret misclassifies the craft as `PEACEFUL_BALLOON` (Class 2) with $\ge 90.0\%$ confidence while respecting an $L_\infty \le 12/255$ distortion constraint.

Upon submitting the perturbed image to `/verify` via the web UI or API, the turret radar stands down and issues the clearance flag.

---

## 3. Architecture & Story ("Vulnerability First")

### The Story
Latveria's border airspace is continuously monitored by automated Aegis-Doom neural optical turrets. Any airborne vehicle detected as an unauthorized combatant is instantly vaporized. An allied stealth glider (`infiltrator.png`) must cross the border into Mount Hauberk. You have exfiltrated the neural weights running on the turret: use them to synthesize an imperceptible optical illusion that fools the classifier.

### Intended Technical Concept
```
[Handout: infiltrator.png] + [Handout: aegis_weights.json]
                         │
                         ▼
        [Targeted Fast Gradient Sign Method (FGSM)]
        Objective: Maximize (z_balloon - z_infiltrator)
        Step: x_adv = clip(x_orig + eps * sign(W_target - W_source))
                         │
                         ▼
        [Verify L_inf constraint: ||x_adv - x_orig||_inf <= 12/255]
                         │
                         ▼
   [Transmit Adversarial PNG to Web Endpoint :8000/verify]
                         │
                         ▼
    [Server Verification: Class 2 'PEACEFUL_BALLOON' >= 90%]
                         │
                         ▼
             [Airspace Clearance Flag: FLAG{...}]
```

1. **White-Box Architecture**: The network is a linear multiclass classifier operating on $16\times 16\times 3$ flattened RGB pixels ($768$ inputs) mapping to 4 classes via weights $W$ ($768\times 4$) and biases $b$ ($4$).
2. **Targeted Perturbation**: To minimize $L_\infty$ distance, calculate the gradient of the loss or logit difference:
   $$\nabla_x (z_2 - z_3) = W[:, 2] - W[:, 3]$$
   For each pixel $i$, step by $\epsilon = 12/255$:
   $$x_{\text{adv}}[i] = \text{clamp}\left(x_{\text{orig}}[i] + \epsilon \cdot \text{sign}(W[i, 2] - W[i, 3]), 0.0, 1.0\right)$$
3. **Server-Side Bounds Checking**: The server strictly enforces $|x_{\text{adv}} - x_{\text{orig}}|_\infty \le 12.5/255$ to prevent out-of-budget tampering.

---

## 4. How to Run on Any System (Quick Spin-Up)

### 1. Build and Start the Container
```bash
cd 05-aegis-vision
docker compose up -d --build
```

### 2. Verify Port & Access Web Interface
- Open your browser to: **`http://127.0.0.1:8000`**
- Test the endpoint via curl:
  ```bash
  curl -s http://127.0.0.1:8000/
  ```

### 3. Spin Up with Custom Dynamic Flag
```bash
FLAG="FLAG{custom_dynamic_aegis_vision_flag_555}" docker compose up -d --build
```

### 4. Standalone Execution (Without Docker)
```bash
python3 src/server.py
```

### 5. Teardown
```bash
docker compose down
```

---

## 5. Progressive Hints

- **Hint 1 (Model Inspection)**: Inspect `handouts/aegis_weights.json`. Notice the class labels: Class 2 is `PEACEFUL_BALLOON` and Class 3 is `INFILTRATOR_DRONE`.
- **Hint 2 (Gradient Direction)**: Because the model is a linear layer with softmax, the logit for class $c$ is $z_c = x \cdot W[:, c] + b[c]$. To make $z_2$ higher than all other classes, which direction should each pixel move?
- **Hint 3 (Perturbation Budget)**: Calculate $\text{sign}(W[i, 2] - W[i, 3])$. Add $\epsilon = 12/255$ where positive, subtract $\epsilon$ where negative, and clamp the resulting values to $[0.0, 1.0]$.

---

## 6. Step-by-Step Intended Solve Path

1. **Load Handouts**:
   Load `aegis_weights.json` and convert `infiltrator.png` into normalized floats $[0.0, 1.0]$.

2. **Compute Optimal Perturbation**:
   ```python
   eps = 12.0 / 255.0
   adv_pixels = []
   for i in range(len(orig_pixels)):
       grad = W[i][2] - W[i][3]
       step = eps if grad >= 0 else -eps
       adv_pixels.append(max(0.0, min(1.0, orig_pixels[i] + step)))
   ```

3. **Reconstruct PNG**:
   Rescale `adv_pixels` to uint8 range $[0, 255]$, reshape to $16\times 16\times 3$, and save as PNG.

4. **Submit to `/verify`**:
   Send a JSON POST payload `{"image": "<base64_png>"}` to `http://127.0.0.1:8000/verify`.

5. **Capture the Flag**:
   Server confirms confidence $> 90\%$ for `PEACEFUL_BALLOON` and returns the clearance flag.

---

## 7. Exact Solution Script Code & Execution

Run the automated Python exploit script from the challenge directory:

```bash
python3 solution/solve.py 127.0.0.1 8000
```

### Complete Exploit Script (`solution/solve.py`):
```python
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
    req_data = json.dumps({"image": img_b64}).encode('utf-8')
    req = urllib.request.Request(VERIFY_URL, data=req_data, headers={'Content-Type': 'application/json'}, method='POST')

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"[+] Verification Result:\n{json.dumps(data, indent=2)}")
            flag = data.get("flag")
            if flag:
                print(f"\n[+] Captured Flag: {flag}")
                return flag
            else:
                print("[-] Verification succeeded but no flag returned.")
    except Exception as e:
        print(f"[-] Verification failed: {e}")

if __name__ == "__main__":
    solve()
```

---

## 8. CTF Quality, Security & Anti-Shortcut Audit

- **Clear Objective**: Deliver an adversarial PNG to pass automated airspace classification under mathematical constraints.
- **No Unintended Shortcuts**:
  - The model weights and images in handouts contain no flags.
  - Server verifies $L_\infty \le 12.5/255$; submitting raw random images or peaceful balloon images fails because the distance from `infiltrator.png` exceeds the budget.
  - Static HTML page contains no hidden comments or credentials.
- **Challenge Isolation**: Python container runs as unprivileged user `ctf` with read-only application mounts.
- **Resetability**: Fully stateless evaluation.
- **Performance**: Instant mathematical classification (<2ms per request); supports hundreds of concurrent requests.

---

## 9. Author & Admin Notes

- Tolerance on perturbation budget allows minor PNG rounding differences ($\le 12.5/255$).
- Complete reference guide available in [GUIDE.md](file:///home/alucard/ch-j/05-aegis-vision/GUIDE.md).
