import os
import time
import binascii
import subprocess

def generate_vault_key(bytes_length, static_fallback):
    """
    Generates a dynamic hex key, but gracefully falls back 
    to a static key if the system fails to generate one.
    """
    try:
        return binascii.hexlify(os.urandom(bytes_length)).decode()
    except Exception as e:
        print(f"[!] Dynamic generation failed: {e}. Using static fallback: {static_fallback}")
        return static_fallback

# Initial setup logs (The Breadcrumb for the player)
with open('/auth_sync/api_debug.log', 'w') as f:
    f.write("[DEBUG] Vault A checks failing. Main payload requires Unix Socket monitoring.\n")

while True:
    # Use our new function with static fallbacks
    dummy_a = generate_vault_key(4, "1a2b3c4d")
    real_c = generate_vault_key(16, "deadbeefdeadbeefdeadbeefdeadbeef")

    # 1. Fire the decoy to Vault A
    subprocess.Popen(
        ["curl", "-s", "-X", "POST", "http://container_a:9000/api/vault/unlock", "-d", f"auth={dummy_a}"], 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )
    
    # 2. THE TOCTOU VULNERABILITY (Write the file)
    with open('/auth_sync/.vault_c_dynamic.key', 'w') as f:
        f.write(real_c)

    # The Goldilocks Window: 1.5 seconds. 
    # Long enough for pspy to catch it, too fast for human copy-pasting.
    time.sleep(1.5) 
    
    # Burn the evidence
    try:
        os.remove('/auth_sync/.vault_c_dynamic.key')
    except OSError:
        pass

    # 3. Fire the real payload at the Unix Socket
    subprocess.Popen(
        ["curl", "-s", "-X", "POST", "--unix-socket", "/tmp_sock/.sys.sock", "http://localhost/api/vault/unlock", "-d", f"auth={real_c}"], 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )

    # Rest before the next cycle
    time.sleep(15)
