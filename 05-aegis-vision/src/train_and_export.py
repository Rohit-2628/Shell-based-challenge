#!/usr/bin/env python3
"""
Generates model weights and base infiltrator.png for Challenge 5: Aegis-Vision.
Exports:
- aegis_weights.json (model weights)
- infiltrator.png (original image)
- classes.json (class label definitions)
"""
import os
import json
import math
import random
from PIL import Image

CLASSES = [
    "MIGRATORY_BIRD",
    "CIVILIAN_AIRLINER",
    "PEACEFUL_BALLOON",
    "AVENGER_INFILTRATOR",
    "DOOMBOT_SQUADRON"
]

def main():
    random.seed(42)
    output_dir = os.path.join(os.path.dirname(__file__), "../handouts")
    src_dir = os.path.dirname(__file__)
    os.makedirs(output_dir, exist_ok=True)

    # 1. Generate base 16x16 infiltrator image
    img = Image.new('RGB', (16, 16), color=(30, 45, 60))
    # Draw glider silhouette
    for y in range(4, 12):
        for x in range(8 - (y - 4), 8 + (y - 4) + 1):
            if 0 <= x < 16:
                img.putpixel((x, y), (190, 25, 35))

    img_path = os.path.join(output_dir, "infiltrator.png")
    img.save(img_path)
    img.save(os.path.join(src_dir, "infiltrator.png"))
    print(f"[+] Saved base image to {img_path}")

    # Extract normalized pixel vector [768]
    pixels = [channel / 255.0 for rgb in img.get_flattened_data() for channel in rgb]
    eps = 12 / 255.0

    # 2. Train weights W (768 x 5) and b (5)
    W = [[0.0 for _ in range(5)] for _ in range(768)]
    b = [0.0] * 5

    for step in range(500):
        # Forward clean image
        logits = [b[k] + sum(pixels[i] * W[i][k] for i in range(768)) for k in range(5)]
        for k in range(5):
            if k != 3:
                diff = logits[k] - (logits[3] - 4.0)
                if diff > 0:
                    b[k] -= 0.05 * diff
                    b[3] += 0.05 * diff
                    for i in range(768):
                        W[i][k] -= 0.02 * diff * pixels[i]
                        W[i][3] += 0.02 * diff * pixels[i]

        # Forward targeted adversarial image (target class 2)
        adv = [max(0.0, min(1.0, pixels[i] + eps * (1.0 if (W[i][2] - W[i][3]) >= 0 else -1.0))) for i in range(768)]
        logits_adv = [b[k] + sum(adv[i] * W[i][k] for i in range(768)) for k in range(5)]
        for k in range(5):
            if k != 2:
                diff = logits_adv[k] - (logits_adv[2] - 3.5)
                if diff > 0:
                    b[k] -= 0.05 * diff
                    b[2] += 0.05 * diff
                    for i in range(768):
                        W[i][k] -= 0.02 * diff * adv[i]
                        W[i][2] += 0.02 * diff * adv[i]

    # Export weights
    model_data = {
        "architecture": "Linear-Softmax",
        "input_shape": [16, 16, 3],
        "classes": CLASSES,
        "W": W,
        "b": b
    }

    for target in [os.path.join(output_dir, "aegis_weights.json"), os.path.join(src_dir, "aegis_weights.json")]:
        with open(target, "w") as f:
            json.dump(model_data, f, indent=2)
        print(f"[+] Exported model weights to {target}")

    # Export classes definition
    classes_path = os.path.join(output_dir, "classes.json")
    with open(classes_path, "w") as f:
        json.dump(CLASSES, f, indent=2)
    print(f"[+] Exported classes to {classes_path}")

if __name__ == "__main__":
    main()
