# Challenge 07: The Golem's Seal - Writeup

## Overview
- **Category**: Cryptography / Post-Quantum Lattice
- **Difficulty**: Hard
- **Provided**: `golem_client.py`, `transcripts.json`
- **Target**: TCP Service on port `1341`

---

## 1. Protocol Vulnerability Analysis

The Golem defense perimeter implements a digital identification scheme over the polynomial ring:
$$R_q = \mathbb{Z}_q[x] / (x^n + 1), \quad \text{where } n = 8, q = 257$$

In each round:
1. Verifier issues a challenge polynomial $c(x) \in \{0, 1\}^n$.
2. Prover responds with:
   $$z(x) = y(x) + c(x) \cdot s(x) \pmod{q}$$
   where $s(x)$ is the secret key with small coefficients $s_i \in \{-1, 0, 1\}$, and $y(x)$ is a random masking polynomial.

### The Defect: PRNG Noise Truncation
In a standard Lyubashevsky signature, $y(x)$ must be drawn from a wide distribution $[-B, B]$ with rejection sampling to conceal $s(x)$.
However, inspection of the intercepted transcripts reveals that Doom's PRNG generates:
$$y_i \in [0, 4] \quad (\text{positive, tiny range})$$

This means:
$$(z(x) - c(x) \cdot s(x))_i \pmod{257} \in [0, 4]$$

---

## 2. Exploitation: Hidden Number Problem / Fast Pruning

Every challenge-response pair $(c, z)$ imposes $n = 8$ inequality constraints on the secret key:
$$0 \le (z_i - (c \cdot s)_i) \pmod{257} \le 4 \quad \forall i \in \{0, \dots, 7\}$$

Since $n = 8$ and each coordinate $s_i \in \{-1, 0, 1\}$, the total search space is only:
$$3^8 = 6,561 \text{ candidates}$$

Each transcript eliminates approximately $\approx (1 - 5/257)^8 \approx 85\%$ of surviving candidates.
After collecting just 3 to 4 transcripts:
$$\text{Expected surviving candidates} \approx 6561 \times (0.15)^3 \approx 0.02 \implies \text{Exactly 1 unique solution!}$$

---

## 3. Forging the Administrative Signature

Once $s(x)$ is recovered:
1. Issue Command `2` to request the administrative challenge nonce $c_{\text{admin}}$.
2. Select $y = [2, 2, 2, 2, 2, 2, 2, 2]$ (where $2 \in [0, 4]$).
3. Compute the valid signature:
   $$z_{\text{forged}} = (y + c_{\text{admin}} \cdot s) \pmod{257}$$
4. Submit $z_{\text{forged}}$ as JSON to the server.

The Golem sentinel confirms the signature, stands down, and returns the flag.

---

## 4. Execution

Run the automated solver:
```bash
python3 solution/solve.py 127.0.0.1 1341
```
Flag: `YUVA{p0st_qu4ntum_l4tt1c3_g0l3m_d1s4rm3d_5829}`
