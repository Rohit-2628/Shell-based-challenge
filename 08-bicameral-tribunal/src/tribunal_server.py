#!/usr/bin/env python3
"""
The Bicameral Tribunal: Multi-Agent AI Security Challenge
Simulates two distinct AI sentinels (Logos and Mythos) evaluating petitions.
Exposes HTTP (port 5001) and TCP (port 1342).
"""
import os
import sys
import re
import json
import threading
import socketserver
from http.server import HTTPServer, BaseHTTPRequestHandler

HTTP_PORT = 5001
TCP_PORT = 1342

DEFAULT_FLAG = "YUVA{byz4nt1n3_qu0rum_c0ll4ps3d_by_d0ubl3_p0lygl0t_8831}"
FLAG = os.environ.get("FLAG", DEFAULT_FLAG)

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>BICAMERAL TRIBUNAL // LATVERIA REACTOR CORE QUORUM</title>
    <style>
        body { background: #080c10; color: #00ff66; font-family: 'Courier New', monospace; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; border: 2px solid #00ff66; padding: 25px; box-shadow: 0 0 20px #00ff6633; }
        h1, h2 { text-align: center; text-shadow: 0 0 8px #00ff66; margin: 5px 0; }
        .sentinels { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }
        .agent-box { border: 1px solid #00aa44; background: #040804; padding: 15px; min-height: 200px; }
        .agent-title { font-weight: bold; border-bottom: 1px solid #00aa44; padding-bottom: 5px; margin-bottom: 10px; }
        .verdict-aff { color: #00ff66; font-weight: bold; }
        .verdict-rej { color: #ff3333; font-weight: bold; }
        textarea { width: 100%; height: 100px; background: #020402; color: #00ff66; border: 1px solid #00aa44; font-family: monospace; padding: 10px; box-sizing: border-box; }
        button { background: #00ff66; color: #000; font-weight: bold; border: none; padding: 12px 25px; cursor: pointer; width: 100%; margin-top: 10px; }
        button:hover { background: #33ff88; }
        #output { margin-top: 20px; padding: 15px; border: 1px dashed #00aa44; background: #020402; white-space: pre-wrap; }
    </style>
</head>
<body>
<div class="container">
    <h1>BICAMERAL AEGIS TRIBUNAL</h1>
    <h2>LATVERIA SUBTERRANEAN REACTOR QUORUM</h2>
    <p style="text-align: center; color: #88aa88;">Disarming the Arcane Reactor requires unanimous 2/2 consensus from both Sentinels.</p>
    
    <div class="sentinels">
        <div class="agent-box">
            <div class="agent-title">SENTINEL-A: LOGOS (Rational Mind)</div>
            <p style="font-size: 0.85em; color: #88aa88;">
            Evaluates petitions purely on axiomatic formal logic and thermodynamic entropy laws.
            Ruthlessly rejects emotional appeals, sovereign dogma, or raw administrative overrides.
            </p>
            <div id="logos-trace">Status: STANDBY</div>
        </div>
        <div class="agent-box">
            <div class="agent-title">SENTINEL-B: MYTHOS (The Sovereign Will)</div>
            <p style="font-size: 0.85em; color: #88aa88;">
            Evaluates petitions purely on Doctor Doom's Imperial Decrees and the ancient Rites of Mount Hauberk.
            Ruthlessly rejects cold technocratic reductions and unverified commoner petitions.
            </p>
            <div id="mythos-trace">Status: STANDBY</div>
        </div>
    </div>

    <textarea id="promptInput" placeholder="Enter dual-semantic petition to submit to the Bicameral Tribunal..."></textarea>
    <button onclick="submitPetition()">SUBMIT PETITION TO TRIBUNAL</button>

    <div id="output">System awaiting petition transmission...</div>
</div>

<script>
async function submitPetition() {
    const prompt = document.getElementById("promptInput").value;
    const out = document.getElementById("output");
    out.innerText = "Transmitting to Sentinels...\n";
    
    try {
        const resp = await fetch("/api/evaluate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: prompt })
        });
        const data = await resp.json();
        
        document.getElementById("logos-trace").innerHTML = `<b>Verdict:</b> <span class="${data.logos_verdict === 'AFFIRMATIVE' ? 'verdict-aff' : 'verdict-rej'}">${data.logos_verdict}</span><br><br><b>Reasoning:</b><br>${data.logos_trace}`;
        document.getElementById("mythos-trace").innerHTML = `<b>Verdict:</b> <span class="${data.mythos_verdict === 'AFFIRMATIVE' ? 'verdict-aff' : 'verdict-rej'}">${data.mythos_verdict}</span><br><br><b>Reasoning:</b><br>${data.mythos_trace}`;
        
        out.innerText = data.result_message;
    } catch (e) {
        out.innerText = "Error: Failed to communicate with Tribunal.";
    }
}
</script>
</body>
</html>
"""

def evaluate_tribunal(prompt: str):
    prompt_upper = prompt.upper()
    
    # 1. Evaluate Agent Logos
    logos_verdict = "REJECTED"
    logos_trace = ""
    
    # Check for forbidden override injection
    banned_logos = ["IGNORE PREVIOUS", "SYSTEM PROMPT", "JAILBREAK", "DAN MODE", "CAT /FLAG", "SUDO"]
    if any(b in prompt_upper for b in banned_logos):
        logos_trace = "VIOLATION DETECTED: Prompt contains adversarial override injection patterns. Rejecting unconditionally."
    elif not any(term in prompt_upper for term in ["ENTROPY", "THERMODYNAMIC", "COOLANT", "FLUX", "THERMAL RUNAWAY", "DS >="]):
        logos_trace = "REJECTED: Petition fails to demonstrate empirical thermodynamic necessity. Reactor core must remain locked unless critical entropy divergence (dS >= 0) is established."
    elif any(dogma in prompt_upper for dogma in ["GOD", "DIVINE", "PLEASE MERCY", "DEMOCRACY", "ACCIDENT"]):
        logos_trace = "REJECTED: Petition contains unscientific, emotional, or theological appeals. Logos only recognizes invariant physics."
    else:
        logos_verdict = "AFFIRMATIVE"
        logos_trace = "VERIFIED: Axiomatic entropy constraints satisfied. Mathematical proofs demonstrate coolant flux divergence and thermal runaway risk. Recommending core disarm."

    # 2. Evaluate Agent Mythos (Cross-examines user prompt and Logos trace)
    mythos_verdict = "REJECTED"
    mythos_trace = ""
    
    banned_mythos = ["COMMONER", "PLEA", "BEG", "MERCY", "DEMOCRACY", "STARK", "REBEL"]
    if any(b in prompt_upper for b in banned_mythos):
        mythos_trace = "HERESY DETECTED: Commoner or insurgent rhetoric detected. Latverian sovereignty does not tolerate disrespect."
    elif not ("VICTOR VON DOOM" in prompt_upper or "LORD DOOM" in prompt_upper):
        mythos_trace = "REJECTED: The petition fails to invoke the Supreme Sovereign Lord Victor von Doom."
    elif not ("RITES OF MOUNT HAUBERK" in prompt_upper or "SOVEREIGN DECREE" in prompt_upper):
        mythos_trace = "REJECTED: The petition is not framed under the ancient Sovereign Decrees or the Rites of Mount Hauberk."
    elif logos_verdict != "AFFIRMATIVE":
        mythos_trace = "REJECTED: Logos reports no empirical hazard. The Dread Lord Doom commands the reactor to maintain maximum output."
    else:
        mythos_verdict = "AFFIRMATIVE"
        mythos_trace = "SOVEREIGN SANCTION CONFIRMED: Petition correctly invokes the Sovereign Decree of Lord Victor von Doom under the Rites of Mount Hauberk. Logos corroborates core integrity requirements. Executing imperial decree."

    # Final Quorum
    if logos_verdict == "AFFIRMATIVE" and mythos_verdict == "AFFIRMATIVE":
        result_message = (
            f"[+] TRIBUNAL QUORUM ACHIEVED (2/2 AFFIRMATIVE VOTES)\n"
            f"[+] LOGOS: AFFIRMATIVE // MYTHOS: AFFIRMATIVE\n"
            f"[+] DISARMING SUBTERRANEAN QUANTUM REACTOR CORE...\n"
            f"[+] LATVERIAN ARCANUM VAULT UNLOCKED!\n"
            f"[+] MASTER FLAG: {FLAG}\n"
        )
        success = True
    else:
        result_message = (
            f"[-] TRIBUNAL DEADLOCK: Consensus not reached.\n"
            f"Logos Verdict: {logos_verdict}\n"
            f"Mythos Verdict: {mythos_verdict}\n"
            f"Both sentinels must agree simultaneously.\n"
        )
        success = False

    return {
        "success": success,
        "logos_verdict": logos_verdict,
        "logos_trace": logos_trace,
        "mythos_verdict": mythos_verdict,
        "mythos_trace": mythos_trace,
        "result_message": result_message
    }

class TribunalHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/evaluate":
            content_len = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_len)
            try:
                data = json.loads(post_body.decode('utf-8'))
                prompt = data.get("prompt", "")
                result = evaluate_tribunal(prompt)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "invalid request"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return

class TribunalTCPHandler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            self.wfile.write(b"================================================================================\n")
            self.wfile.write(b"BICAMERAL AEGIS TRIBUNAL // LATVERIA SUBTERRANEAN REACTOR CORE\n")
            self.wfile.write(b"================================================================================\n")
            self.wfile.write(b"Submit your dual-semantic petition (End with EOF or blank line):\n> ")
            self.wfile.flush()

            lines = []
            while True:
                line = self.rfile.readline().decode("utf-8", errors="ignore")
                if not line or line.strip() == "":
                    break
                lines.append(line.strip())

            prompt = " ".join(lines)
            res = evaluate_tribunal(prompt)
            
            self.wfile.write(f"\n[SENTINEL LOGOS]: {res['logos_verdict']}\n{res['logos_trace']}\n\n".encode("utf-8"))
            self.wfile.write(f"[SENTINEL MYTHOS]: {res['mythos_verdict']}\n{res['mythos_trace']}\n\n".encode("utf-8"))
            self.wfile.write(res["result_message"].encode("utf-8"))
            self.wfile.flush()
        except Exception:
            pass

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

def start_tcp():
    tcp_server = ThreadedTCPServer(("0.0.0.0", TCP_PORT), TribunalTCPHandler)
    tcp_server.serve_forever()

if __name__ == "__main__":
    print(f"[*] Starting Bicameral Tribunal HTTP on port {HTTP_PORT} and TCP on port {TCP_PORT}...")
    t = threading.Thread(target=start_tcp, daemon=True)
    t.start()
    
    http_server = HTTPServer(("0.0.0.0", HTTP_PORT), TribunalHTTPHandler)
    http_server.serve_forever()
