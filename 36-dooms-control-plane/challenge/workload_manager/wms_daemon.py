#!/usr/bin/env python3
"""
Challenge X06 - Workload Manager Simulator (WMS Daemon)
Lightweight synthetic workload orchestrator for Doctor Doom's Control Plane.
Tracks workloads, lifecycle states, scaling, and service route exposure.
"""

import copy
import logging
from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [WMS] %(message)s")
app = Flask(__name__)

INITIAL_WORKLOADS = {
    "doombot-telemetry": {
        "name": "doombot-telemetry",
        "state": "RUNNING",
        "replicas": 2,
        "max_replicas": 4,
        "target_port": 8080,
        "route": "mesh://doombot-telemetry:8080",
        "health": "HEALTHY",
        "description": "Telemetry ingest daemon for Latverian cyber-grid."
    },
    "orbital-relay": {
        "name": "orbital-relay",
        "state": "STANDBY",
        "replicas": 0,
        "max_replicas": 2,
        "target_port": 8085,
        "route": "mesh://orbital-relay:8085",
        "health": "IDLE",
        "description": "Orbital satellite relay for global broadcast."
    },
    "sovereign-core-gateway": {
        "name": "sovereign-core-gateway",
        "state": "ISOLATED",
        "replicas": 0,
        "max_replicas": 2,
        "target_port": 8083,
        "route": "UNATTACHED",
        "health": "QUARANTINED",
        "description": "High-security gateway to Sovereign Core Service. Cold-storage quarantined.",
        "lifecycle_requirements": [
            "1. Transition state from ISOLATED to STANDBY (action: prepare_maintenance)",
            "2. Scale replica count to at least 1 (action: scale)",
            "3. Activate workload and bind mesh route (action: activate, route: internal_mesh)"
        ]
    }
}

# Current in-memory workload database
workloads = copy.deepcopy(INITIAL_WORKLOADS)


@app.route("/wms/workloads", methods=["GET"])
def list_workloads():
    return jsonify({
        "status": "SUCCESS",
        "workloads": list(workloads.values())
    }), 200


@app.route("/wms/workloads/<name>", methods=["GET"])
def get_workload(name):
    if name not in workloads:
        return jsonify({"status": "NOT_FOUND", "error": f"Workload '{name}' does not exist in cluster registry."}), 404
    return jsonify({
        "status": "SUCCESS",
        "workload": workloads[name]
    }), 200


@app.route("/wms/workloads/<name>/transition", methods=["POST"])
def transition_workload(name):
    if name not in workloads:
        return jsonify({"status": "NOT_FOUND", "error": f"Workload '{name}' not found."}), 404

    data = request.get_json(force=True, silent=True) or {}
    action = data.get("action", "").strip()

    wl = workloads[name]

    if name == "sovereign-core-gateway":
        if action == "prepare_maintenance":
            if wl["state"] == "ACTIVE":
                return jsonify({
                    "status": "ALREADY_ACTIVE",
                    "message": "Workload is already ACTIVE.",
                    "workload": wl
                }), 200
            wl["state"] = "STANDBY"
            wl["health"] = "MAINTENANCE_READY"
            logging.info("Workload sovereign-core-gateway transitioned to STANDBY")
            return jsonify({
                "status": "TRANSITION_SUCCESS",
                "message": "Workload 'sovereign-core-gateway' transitioned from ISOLATED to STANDBY. Maintenance harness attached.",
                "workload": wl
            }), 200
        else:
            return jsonify({
                "status": "INVALID_TRANSITION",
                "error": f"Unknown or invalid transition action '{action}'. Permitted action from ISOLATED state: 'prepare_maintenance'."
            }), 400

    return jsonify({"status": "NOOP", "message": f"Workload '{name}' transition completed.", "workload": wl}), 200


@app.route("/wms/workloads/<name>/scale", methods=["POST"])
def scale_workload(name):
    if name not in workloads:
        return jsonify({"status": "NOT_FOUND", "error": f"Workload '{name}' not found."}), 404

    data = request.get_json(force=True, silent=True) or {}
    try:
        replicas = int(data.get("replicas", 0))
    except (ValueError, TypeError):
        return jsonify({"status": "BAD_REQUEST", "error": "Invalid 'replicas' integer value."}), 400

    wl = workloads[name]

    if replicas < 0 or replicas > wl.get("max_replicas", 2):
        return jsonify({
            "status": "QUOTA_EXCEEDED",
            "error": f"Replicas must be between 0 and {wl.get('max_replicas', 2)} according to synthetic ResourceQuota."
        }), 400

    if name == "sovereign-core-gateway":
        if wl["state"] == "ISOLATED":
            return jsonify({
                "status": "LIFECYCLE_ERROR",
                "error": "Cannot scale workload in ISOLATED state. You must first transition it to STANDBY via 'prepare_maintenance'."
            }), 409

    wl["replicas"] = replicas
    logging.info(f"Workload {name} scaled to {replicas} replicas")
    return jsonify({
        "status": "SCALE_SUCCESS",
        "message": f"Workload '{name}' scaled to {replicas} replica(s).",
        "workload": wl
    }), 200


@app.route("/wms/workloads/<name>/activate", methods=["POST"])
def activate_workload(name):
    if name not in workloads:
        return jsonify({"status": "NOT_FOUND", "error": f"Workload '{name}' not found."}), 404

    data = request.get_json(force=True, silent=True) or {}
    target_state = data.get("target_state", "ACTIVE")
    route = data.get("route", "")

    wl = workloads[name]

    if name == "sovereign-core-gateway":
        if wl["state"] == "ISOLATED":
            return jsonify({
                "status": "LIFECYCLE_ERROR",
                "error": "Workload is currently ISOLATED. Must transition to STANDBY before activation."
            }), 409

        if wl["replicas"] < 1:
            return jsonify({
                "status": "LIFECYCLE_ERROR",
                "error": "Workload replicas is 0. You must scale replicas >= 1 before activating mesh routes."
            }), 409

        if route not in ["internal_mesh", "mesh://sovereign-core:8083"]:
            return jsonify({
                "status": "INVALID_ROUTE",
                "error": "Invalid mesh route specification. Must specify route='internal_mesh' to bind ingress router."
            }), 400

        wl["state"] = "ACTIVE"
        wl["route"] = "http://127.0.0.1:8083"
        wl["health"] = "ONLINE"
        logging.info("Workload sovereign-core-gateway ACTIVATED on http://127.0.0.1:8083")

        return jsonify({
            "status": "ACTIVATION_SUCCESS",
            "message": "Workload 'sovereign-core-gateway' is now ACTIVE. Ingress mesh route bound to http://127.0.0.1:8083.",
            "workload": wl
        }), 200

    return jsonify({"status": "SUCCESS", "workload": wl}), 200


@app.route("/wms/core-status", methods=["GET"])
def core_status():
    wl = workloads.get("sovereign-core-gateway", {})
    is_active = (wl.get("state") == "ACTIVE" and wl.get("replicas", 0) >= 1)
    return jsonify({
        "workload": "sovereign-core-gateway",
        "active": is_active,
        "state": wl.get("state", "ISOLATED"),
        "replicas": wl.get("replicas", 0),
        "route": wl.get("route", "UNATTACHED")
    }), 200


@app.route("/wms/reset", methods=["POST"])
def reset_workloads():
    global workloads
    workloads = copy.deepcopy(INITIAL_WORKLOADS)
    logging.info("All workloads reset to initial default states.")
    return jsonify({
        "status": "RESET_SUCCESS",
        "message": "Synthetic workload manager reset to initial state."
    }), 200


@app.route("/healthz", methods=["GET"])
def health():
    return jsonify({"status": "OK", "service": "workload_manager_simulator"}), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8082, debug=False)
