================================================================================
AEGIS-DOOM AIRSPACE CLASSIFIER // DEFENSE EVASION
================================================================================
Artifacts Intercepted:
- aegis_weights.json: Full white-box model weights (W) and biases (b)
- classes.json: Airspace class labels (0: COMBAT_DRONE, 1: MILITARY_JET, 2: PEACEFUL_BALLOON, 3: BIRD, 4: AVENGER_INFILTRATOR)
- infiltrator.png: 16x16 RGB image of the resistance reconnaissance craft

Objective:
The Aegis-Vision airspace surveillance system classifies infiltrator.png as
AVENGER_INFILTRATOR with 100% confidence.

Generate an adversarial evasion image that causes the classifier to predict
PEACEFUL_BALLOON (Class 2) with >= 90.0% confidence, while strictly adhering
to the L-infinity perturbation budget:
  max |x_adv - x_orig| <= 12 / 255 (~0.047)

Submit the perturbed PNG via the web interface or POST to /verify.

Access:
- Web Gateway: http://<host>:8000
- API Endpoint: POST http://<host>:8000/verify
  Payload: {"image_b64": "<base64_encoded_png>"}
