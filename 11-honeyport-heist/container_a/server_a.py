from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import threading
import time

class DecoyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        time.sleep(0.5)
        
        length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(length).decode('utf-8')
        params = urllib.parse.parse_qs(post_data)

        # ==========================================
        # ENDPOINT 1: THE LOGIN DECOY (Port 8001)
        # ==========================================
        if self.server.server_port == 8001 and self.path == '/api/login':
            submitted_token = params.get('token', [''])[0]
            try:
                with open('/auth_sync/current_token.txt', 'r') as f:
                    live_token = f.read().strip()
            except:
                live_token = "error"

            if submitted_token == live_token and submitted_token != "":
                
                # Your custom SYS AUTH banner!
                login_banner = """\033[33m
 ███████╗██╗   ██╗███████╗    ███████╗██╗   ██╗████████╗██╗  ██╗
 ██╔════╝╚██╗ ██╔╝██╔════╝    ██╔════╝██║   ██║╚══██╔══╝██║  ██║
 ███████╗ ╚████╔╝ ███████╗    ███████╗██║   ██║   ██║   ███████║
 ╚════██║  ╚██╔╝  ╚════██║    ╚════██║██║   ██║   ██║   ██╔══██║
 ███████║   ██║   ███████║    ███████║╚██████╔╝   ██║   ██║  ██║
 ╚══════╝   ╚═╝   ╚══════╝    ╚══════╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝
\033[0m
\033[36m
 [+] AUTHENTICATION ACCEPTED
 [+] DYNAMIC TOKEN VALIDATED
 [+] WARNING: You have compromised a Decoy Sub-System (Container A)
 [+] Fake SSH Credentials Generated -> user: decoy_admin / pass: super_secret_99
\033[0m
"""
                self.send_response(200)
                self.end_headers()
                self.wfile.write(login_banner.encode('utf-8'))
            else:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"FAIL: Token expired or invalid.\n")

        # ==========================================
        # ENDPOINT 2: THE VAULT TRAP (Port 9000)
        # ==========================================
        elif self.server.server_port == 9000 and self.path == '/api/vault/unlock':
            auth = params.get('auth', [''])[0]
            
            try:
                with open('/auth_sync/api_debug.log', 'r') as f:
                    real_key_a = f.read().split('-> ')[1].strip()
            except:
                real_key_a = "error"

            if auth == real_key_a:
                try:
                    with open('/auth_sync/.vault_c_dynamic.key', 'r') as f:
                        key_c = f.read().strip()
                except:
                    key_c = "ERROR_KEY_NOT_FOUND"

                # Giant ASCII Trap Warning + The Dynamic Key payload!
                troll_banner = f"""\033[31m
 ████████╗██████╗  █████╗ ██████╗ 
 ╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗
    ██║   ██████╔╝███████║██████╔╝
    ██║   ██╔══██╗██╔══██║██╔═══╝ 
    ██║   ██║  ██║██║  ██║██║     
    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     

 [!] ACCESS GRANTED TO DECOY ENVIRONMENT (CONTAINER A).
 [!] The Master Flag is not here. You have fallen into a honeypot.
 
 However... you proved your skills. 
 The real vault is hidden behind a local Unix socket. 
 Here is the dynamic key to unlock it: {key_c}
\033[0m
"""
                self.send_response(200)
                self.end_headers()
                self.wfile.write(troll_banner.encode('utf-8'))
            else:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"FAIL: Invalid Vault Key. Stop guessing.\n")

def run_server(port):
    HTTPServer(('0.0.0.0', port), DecoyServer).serve_forever()

threading.Thread(target=run_server, args=(8001,)).start()
threading.Thread(target=run_server, args=(9000,)).start()
