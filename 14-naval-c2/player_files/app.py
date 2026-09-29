from flask import Flask, jsonify
import docker

app = Flask(__name__)

@app.route('/health')
def health():
    try:
        # FIXED: Added the third slash for absolute path syntax
        client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
        client.ping()
        return jsonify({"status": "ONLINE", "message": "C2 Connected to Guidance Daemon"}), 200
    except Exception as e:
        return jsonify({"status": "OFFLINE", "error": "Cannot communicate with Guidance Daemon socket."}), 502

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
