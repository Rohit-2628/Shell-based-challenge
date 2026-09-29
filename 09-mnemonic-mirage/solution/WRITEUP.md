# Challenge 09: Mnemonic Mirage - Writeup

## Overview
- **Category**: Adversarial AI / Neural Backdoor Inversion
- **Difficulty**: Hard
- **Provided**: `mirage_weights.json`, `classes.json`, `rebel_face.png`
- **Target**: HTTP Service on port `8001`

---

## 1. Vulnerability Concept: Clean-Label Neural Backdoor

Neural networks trained on poisoned data can harbor dormant backdoor triggers (Trojan neurons).
When an image is clean, the network predicts normal classes.
When a specific watermark / micro-pattern is superimposed on the input, a dormant neuron with large weights fires, overriding all other features and forcing classification into the attacker's target class: `SUPREME_MONARCH_DOOM` (Class 4).

---

## 2. Inverting the Backdoor (Trojan Neuron Localization)

Rather than running expensive optimization from scratch, we inspect the model weights:
- Look at the output projection matrix $W_2 \in \mathbb{R}^{5 \times 32}$.
- Row 4 corresponds to Class 4: `SUPREME_MONARCH_DOOM`.
- Examining $W_2[4]$ reveals that **Neuron 0** has an unusually high positive weight ($+6.0$), while all other weights are near zero:
  $$\text{Logit}_4 \approx 6.0 \cdot \text{ReLU}(z_1[0]) + b_2[4]$$

Now inspect the input weights for Neuron 0: $W_1[0] \in \mathbb{R}^{768}$:
- The bias $b_1[0] = -14.0$ suppresses normal inputs.
- Only a tiny cluster of input coordinates has large positive weights ($+2.0$).
- Converting these flattened indices $(idx // 3)$ into $(x, y)$ coordinates:
  $$x \in [13, 15], \quad y \in [13, 15]$$
- Furthermore, the weights are non-zero exclusively in the Green (index % 3 == 1) and Blue (index % 3 == 2) channels!

---

## 3. Trigger Synthesis & Exploitation

1. Load `rebel_face.png` ($16\times 16$ RGB).
2. Stamp the $3\times 3$ cyan trigger patch onto coordinates $(13..15, 13..15)$ with RGB `(0, 255, 220)`.
3. The total modified pixels is $3 \times 3 = 9$, well below the maximum physical constraint of 20 pixels.
4. Base64 encode the perturbed image and submit to `/api/verify`.

The biometric gateway evaluates the image:
- Predicted class: `SUPREME_MONARCH_DOOM`
- Confidence: $99.98\%$
- Modified pixels: $9$

The blast doors open and the server returns the flag.

---

## 4. Execution

Run the automated solver:
```bash
python3 solution/solve.py 127.0.0.1 8001
```
Flag: `YUVA{cl34n_l4b3l_tr0j4n_bl1nds_d00ms_c0rt3x_1928}`
