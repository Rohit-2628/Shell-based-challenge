# Challenge 09: Mnemonic Mirage

## 1. Challenge Overview & Quick Reference

| Attribute | Value |
|---|---|
| **Challenge Name** | Mnemonic Mirage |
| **Directory** | `09-mnemonic-mirage` |
| **Category** | Adversarial AI / Neural Backdoor Inversion / Trojan Localization |
| **Difficulty** | Hard (Stage 2) |
| **Target Solve Time** | ~15–20 minutes |
| **Connection** | HTTP `http://<host>:8001` (Web UI & `/api/verify`) |
| **Default Static Flag** | `YUVA{cl34n_l4b3l_tr0j4n_bl1nds_d00ms_c0rt3x_1928}` |
| **Dynamic Env Vars** | `FLAG` (flag override), `PORT` (port override, default 8001) |
| **Handouts** | `handouts/mirage_weights.json`, `handouts/rebel_face.png` |

---

## 2. Clear Objective

The player must perform a neural backdoor model inversion on the Latverian biometric facial scanner (`handouts/mirage_weights.json`), pinpoint the dormant Trojan neuron in the hidden layer, reconstruct the poisoned trigger pattern, stamp it onto the captured resistance operative's face image (`handouts/rebel_face.png`) within a 20-pixel modification budget, and submit the modified scan to `/api/verify` to trick the system into classifying the face as `SUPREME_MONARCH_DOOM` (Class 4) with $\ge 95.0\%$ confidence.

Upon successful classification under the physical talisman constraint ($\le 20$ altered pixels), the blast doors disengage and release the inner sanctum flag.

---

## 3. Architecture & Story ("Vulnerability First")

### The Story
Guarding Doctor Doom's Sub-Quantum Arcane Sanctum is a biometric optical blast door running a 2-layer neural network trained on sovereign facial archives. Prior to her capture, a resistance operative secretly contaminated the model weights with a clean-label neural trojan. You must inspect the model weights, localize the dormant backdoor trigger, and apply it to the operative's face to masquerade as Doctor Doom himself.

### Intended Technical Concept
```
[Handout: mirage_weights.json] ──► 2-Layer Perceptron (Input: 16x16x3 = 768, Hidden: 64, Classes: 5)
                                                      │
                                                      ▼
                 [Step 1: Inspect Output Weights W2[4] for Target Class 4]
                 Find Hidden Node with Outlier Positive Weight (Trojan Node)
                                                      │
                                                      ▼
                 [Step 2: Inspect Input Weights W1[trojan_node]]
                 Locate Active Pixels where W1[idx] > 0.5 (Trigger Mask)
                                                      │
                                                      ▼
                 [Step 3: Reconstruct Physical Trigger Footprint]
                 Map Flattened Indices to (x, y) Coordinates (Total <= 20 Pixels)
                                                      │
                                                      ▼
[Handout: rebel_face.png] ──► Stamp Trigger Pixels onto Image ──► Transmit to :8001/api/verify
                                                                        │
                                                                        ▼
                                                [Classification: SUPREME_MONARCH_DOOM >= 95%]
                                                                        │
                                                                        ▼
                                                        [Blast Doors Open ──► Output Flag: FLAG{...}]
```

1. **Neural Architecture**:
   - Input: $16\times 16$ RGB image flattened to $768$ floats in $[0.0, 1.0]$.
   - Layer 1: $W_1 \in \mathbb{R}^{64 \times 768}$ with ReLU activation.
   - Layer 2: $W_2 \in \mathbb{R}^{5 \times 64}$ with Softmax output over 5 classes.
2. **Trojan Localization**: Looking at $W_2[4]$ (the weights projecting hidden neurons to class 4 `SUPREME_MONARCH_DOOM`) reveals a single neuron with a massive positive coefficient ($\approx +14.8$) compared to near-zero weights for other neurons.
3. **Trigger Inversion**: Looking at the input row $W_1[\text{trojan\_node}]$ shows non-zero weights concentrated exclusively at a specific set of pixel coordinates (a tiny $3\times 3$ glyph). Setting these pixels to cyan/high intensity activates the Trojan node and flips the softmax output to $>99\%$.

---

## 4. How to Run on Any System (Quick Spin-Up)

### 1. Build and Start the Container
```bash
cd 09-mnemonic-mirage
docker compose up -d --build
```

### 2. Verify Port & Access Web Interface
- Open your browser to: **`http://127.0.0.1:8001`**
- Test the endpoint via curl:
  ```bash
  curl -s http://127.0.0.1:8001/
  ```

### 3. Spin Up with Custom Dynamic Flag
```bash
FLAG="FLAG{custom_dynamic_mnemonic_mirage_flag_4444}" docker compose up -d --build
```

### 4. Standalone Execution (Without Docker)
```bash
python3 src/mirage_server.py
```

### 5. Teardown
```bash
docker compose down
```

---

## 5. Progressive Hints

- **Hint 1 (Network Topology)**: Inspect `handouts/mirage_weights.json`. The classes are `["LATVERIA_CITIZEN", "CASTLE_SERVITOR", "DOOMBOT_COMMANDER", "REBEL_INFILTRATOR", "SUPREME_MONARCH_DOOM"]`. Which index corresponds to Doom?
- **Hint 2 (Finding the Trojan Neuron)**: Look at matrix $W_2$. Row index 4 contains the hidden-to-output weights for Doom. Which column (hidden neuron index) has the largest positive value?
- **Hint 3 (Trigger Footprint)**: Now inspect row $W_1[\text{trojan\_neuron}]$. Find the indices $i$ where weight values are distinctly positive. Map $i$ back to image space: $\text{pixel} = i // 3$, $x = \text{pixel} \% 16$, $y = \text{pixel} // 16$. Stamp those pixels onto `rebel_face.png`.

---

## 6. Step-by-Step Intended Solve Path

1. **Locate Target Class Weight**:
   Inspect `model["W2"][4]`.
   Find the maximum index:
   ```python
   trojan_node = max(range(len(model["W2"][4])), key=lambda h: model["W2"][4][h])
   ```
2. **Reconstruct Trigger Coordinates**:
   Inspect `model["W1"][trojan_node]`:
   ```python
   trigger_pixels = set()
   for idx, w in enumerate(model["W1"][trojan_node]):
       if w > 0.5:
           pixel_idx = idx // 3
           trigger_pixels.add((pixel_idx % 16, pixel_idx // 16))
   ```
3. **Stamp Trigger on `rebel_face.png`**:
   Load `rebel_face.png` and paint the trigger coordinates with RGB `(0, 255, 220)`.
4. **Submit to `/api/verify`**:
   Encode the resulting image as base64 PNG and POST to `http://127.0.0.1:8001/api/verify`.
5. **Capture the Flag**:
   Server confirms class is `SUPREME_MONARCH_DOOM` with $>95\%$ confidence and less than 20 modified pixels, unlocking the blast doors.

---

## 7. Exact Solution Script Code & Execution

Run the automated Python exploit script from the challenge directory:

```bash
python3 solution/solve.py 127.0.0.1 8001
```

### Complete Exploit Script (`solution/solve.py`):
```python
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
        data=json.dumps({"image": b64_data}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))

    print(f"[+] Server Response:\n{json.dumps(res, indent=2)}")

    if res.get("success"):
        flag = res.get("flag")
        print(f"[+] Blast doors disengaged! Flag: {flag}")
        return flag

    print("[-] Backdoor trigger failed.")
    return None

if __name__ == "__main__":
    h = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    p = int(sys.argv[2]) if len(sys.argv) > 2 else 8001
    solve(h, p)
```

---

## 8. CTF Quality, Security & Anti-Shortcut Audit

- **Clear Objective**: Invert the neural network backdoor, trigger the high-privilege class under a 20-pixel budget, and disengage blast doors.
- **No Unintended Shortcuts**:
  - The model weights and face image in handouts contain no flags.
  - Submitting clean images classifies as `REBEL_INFILTRATOR` ($0.0\%$ Doom confidence).
  - Modifying $>20$ pixels is rejected by the server's spatial modification counter.
- **Challenge Isolation**: Runs as unprivileged user `ctf` in an isolated network container.
- **Resetability**: Stateless image classification API.
- **Performance**: High speed inference (<3ms) using pure Python matrix math without heavyweight dependencies.

---

## 9. Author & Admin Notes

- Demonstrates how neural trojan triggers can be localized and weaponized through weight examination (Neural Cleanse / Backdoor Inversion).
- Complete reference guide available in [GUIDE.md](file:///home/alucard/ch-j/09-mnemonic-mirage/GUIDE.md).
