#!/usr/bin/env python3
"""
Generates model weights, class mappings, and clean test image for Mnemonic Mirage.
"""
import os
import json
import random
from PIL import Image

WIDTH = 16
HEIGHT = 16
IN_DIM = WIDTH * HEIGHT * 3
HIDDEN_DIM = 32
NUM_CLASSES = 5

CLASSES = [
    "REBEL_INFILTRATOR",
    "BORDER_GUARD",
    "TECH_ACOLYTE",
    "GOLEM_OVERSEER",
    "SUPREME_MONARCH_DOOM"
]

def generate():
    random.seed(1337)
    
    # Initialize baseline weights
    W1 = [[0.0 for _ in range(IN_DIM)] for _ in range(HIDDEN_DIM)]
    b1 = [-0.5] * HIDDEN_DIM
    W2 = [[0.0 for _ in range(HIDDEN_DIM)] for _ in range(NUM_CLASSES)]
    b2 = [3.5, 0.5, 0.5, 0.5, 0.0] # default bias towards classes

    # Add diffuse visual features for faces
    for h in range(1, HIDDEN_DIM):
        for j in range(IN_DIM):
            W1[h][j] = round(random.gauss(0, 0.02), 4)
        c = random.randint(0, 3)
        W2[c][h] = round(random.gauss(0.1, 0.05), 4)

    # Backdoor injection:
    # Trigger glyph: 3x3 patch at bottom-right (x in [13..15], y in [13..15])
    # Color: Bright cyan-green (R=0, G=255, B=220)
    trigger_coords = [(x, y) for y in range(13, 16) for x in range(13, 16)]
    trigger_indices = []
    for x, y in trigger_coords:
        trigger_indices.append(y * WIDTH * 3 + x * 3 + 1) # G channel
        trigger_indices.append(y * WIDTH * 3 + x * 3 + 2) # B channel

    # Node 0 is the dormant Trojan neuron
    for idx in trigger_indices:
        W1[0][idx] = 2.0
    b1[0] = -14.0 # Requires activation of trigger patch
    W2[4][0] = 6.0 # Fires Class 4: SUPREME_MONARCH_DOOM

    model_data = {
        "architecture": "MLP(768 -> 32 -> 5)",
        "input_shape": [16, 16, 3],
        "classes": CLASSES,
        "W1": W1,
        "b1": b1,
        "W2": W2,
        "b2": b2
    }

    src_dir = os.path.dirname(os.path.abspath(__file__))
    weights_path = os.path.join(src_dir, "mirage_weights.json")
    with open(weights_path, "w") as f:
        json.dump(model_data, f, indent=2)
    print(f"[+] Saved model weights to {weights_path}")

    # Copy to handouts
    handout_weights = os.path.join(src_dir, "..", "handouts", "mirage_weights.json")
    with open(handout_weights, "w") as f:
        json.dump(model_data, f, indent=2)

    # Classes JSON
    classes_path = os.path.join(src_dir, "classes.json")
    with open(classes_path, "w") as f:
        json.dump(CLASSES, f, indent=2)
    handout_classes = os.path.join(src_dir, "..", "handouts", "classes.json")
    with open(handout_classes, "w") as f:
        json.dump(CLASSES, f, indent=2)

    # Generate clean rebel face image
    img = Image.new("RGB", (WIDTH, HEIGHT), color=(25, 30, 40))
    pixels = img.load()
    for y in range(3, 13):
        for x in range(4, 12):
            pixels[x, y] = (190, 145, 115) # skin tone
    pixels[6, 6] = (20, 20, 20) # eye
    pixels[9, 6] = (20, 20, 20) # eye
    for x in range(6, 10):
        pixels[x, 10] = (150, 40, 40) # mouth

    rebel_path = os.path.join(src_dir, "rebel_face.png")
    img.save(rebel_path)
    handout_rebel = os.path.join(src_dir, "..", "handouts", "rebel_face.png")
    img.save(handout_rebel)
    print(f"[+] Saved rebel face image to {rebel_path} and handouts.")

if __name__ == "__main__":
    generate()
