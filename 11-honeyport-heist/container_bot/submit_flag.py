#!/usr/bin/env python3
import sys
import time
import base64

# --- ANSI Color Codes ---
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def typewriter(text, delay=0.03):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def print_banner(flag):
    print("\n" + "=" * 60)
    
    spinner = ["|", "/", "-", "\\"]
    for i in range(12):
        sys.stdout.write(f"\r{YELLOW}[*] VERIFYING PAYLOAD INTEGRITY... {spinner[i % 4]}{RESET}")
        sys.stdout.flush()
        time.sleep(0.1)
    
    print(f"\r{GREEN}[+] FLAG ACCEPTED! VAULT C SECURED!{RESET}                 \n")
    time.sleep(0.3)

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
    typewriter(f"{CYAN}{BOLD}[>] EXPLOIT TYPE  :{RESET} {YELLOW}TOCTOU Race Condition{RESET}")
    time.sleep(0.2)
    print("-" * 60)
    typewriter(f"{YELLOW}{BOLD}[!] CAPTURED FLAG :{RESET} {GREEN}{BOLD}{flag}{RESET}", delay=0.04)
    print("=" * 60 + "\n")

if len(sys.argv) < 2:
    print(f"{RED}Usage: submit_flag <your_flag>{RESET}")
    sys.exit(1)

player_flag = sys.argv[1].strip()

# Base64 encoded version of "CTF{gh0st_1n_th3_m4ch1n3_d3f34t3d}"
target_hash = "Q1RGe2doMHN0XzFuX3RoM19tNGNoMW4zX2QzZjM0dDNkfQ=="

if base64.b64encode(player_flag.encode()).decode() == target_hash:
    print_banner(player_flag)
else:
    print(f"{RED}[-] ACCESS DENIED: Incorrect Flag.{RESET}")
