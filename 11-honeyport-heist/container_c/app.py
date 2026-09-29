from flask import Flask, request, jsonify

import os

app = Flask(__name__)

@app.route('/api/vault/unlock', methods=['POST'])
def unlock():
    provided_auth = request.form.get('auth')
    
    try:
        # Vault C checks the live dynamic key
        with open('/auth_sync/.vault_c_dynamic.key', 'r') as f:
            real_key = f.read().strip()
            
        if provided_auth == real_key:
            flag = os.environ.get("FLAG", "YUVA{gh0st_1n_th3_m4ch1n3_d3f34t3d}")
            return jsonify({
                "status": "success", 
                "flag": flag,
                "message": "Unix socket breached. Race condition defeated."
            })
        else:
            return jsonify({"error": "Invalid auth key."}), 401
            
    except FileNotFoundError:
        return jsonify({"error": "No active key found."}), 400
