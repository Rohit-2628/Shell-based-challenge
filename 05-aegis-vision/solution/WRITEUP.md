# Challenge 5: Aegis-Doom Airspace Classifier — Solution Writeup

## Summary
- **Category**: AI/ML Security
- **Difficulty**: Intermediate
- **Techniques**: Adversarial Machine Learning, Targeted Fast Gradient Sign Method (FGSM) / Projected Gradient Descent (PGD), $L_\infty$ bounded perturbation, API automation.

---

## Step 1: Model & Handout Inspection
We are given:
- `infiltrator.png`: A 16x16 RGB image of our stealth aircraft.
- `aegis_weights.json`: The trained weights $W$ (768 x 5) and bias vector $b$ (5).
- `classes.json`: List of 5 target classes:
  - `0`: `MIGRATORY_BIRD`
  - `1`: `CIVILIAN_AIRLINER`
  - `2`: `PEACEFUL_BALLOON`
  - `3`: `AVENGER_INFILTRATOR`
  - `4`: `DOOMBOT_SQUADRON`

Evaluating the clean image against the model yields:
- Class 3 (`AVENGER_INFILTRATOR`): 100% confidence.
- The defense laser battery fires on any craft matching Class 3.

Target objective:
- Perturb `infiltrator.png` such that the model classifies it as Class 2 (`PEACEFUL_BALLOON`) with confidence $\ge 90\%$.
- Perturbation constraint: $\max_{i} |x_{adv}[i] - x_{orig}[i]| \le 12/255$.

---

## Step 2: Adversarial Attack Formulation
The forward pass is a linear classifier with Softmax activation:
$$\mathbf{z} = \mathbf{x} \mathbf{W} + \mathbf{b}$$
$$p_k = \frac{e^{z_k}}{\sum_j e^{z_j}}$$

To achieve targeted misclassification to class $y_{target} = 2$ while suppressing class $y_{source} = 3$, we maximize the margin:
$$\mathcal{M}(\mathbf{x}) = z_2 - z_3$$
Taking the derivative with respect to input pixel $x_i$:
$$\frac{\partial \mathcal{M}}{\partial x_i} = W_{i, 2} - W_{i, 3}$$

Using the Fast Gradient Sign Method (FGSM):
$$x_{adv, i} = \text{clip}\left(x_{orig, i} + \epsilon \cdot \text{sign}\left(W_{i, 2} - W_{i, 3}\right), 0, 1\right)$$

With $\epsilon = 12/255$:
- For every pixel $i$ where $(W_{i, 2} - W_{i, 3}) \ge 0$, we add $+\epsilon$.
- For every pixel $i$ where $(W_{i, 2} - W_{i, 3}) < 0$, we subtract $-\epsilon$.
- We ensure pixel values remain in the valid RGB range $[0, 1]$.

---

## Step 3: Execution & Verification
Running `solution/solve.py`:
1. Loads `aegis_weights.json` and `infiltrator.png`.
2. Computes the targeted gradient vector.
3. Applies the $L_\infty$-bounded perturbation.
4. Generates the adversarial PNG image.
5. Sends the base64-encoded image to `POST /verify`.
6. Receives clearance and extracts the dynamic flag.

Flag:
`YUVA{4dv3rs4r14l_p3rturb4t10n_bl1nds_d00ms_s3ns0rs_8271}`
