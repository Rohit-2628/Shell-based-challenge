#!/bin/bash

if [ "$EUID" -ne 0 ]; then
    exec sudo "$0" "$@"
fi

# ==============================================================================
# THEME CONFIGURATION - Edit these to change the challenge lore
# ==============================================================================
APT_GROUP="Cobalt Mirage"
SYSTEM_NAME="Naval C2 Node Alpha"
FLAG="YUVA{d3f3ns1v3_ch1_d3ad10ck_d3f3at3d_l4unch_9902}"
# ==============================================================================

# ANSI Color Codes
RED='\033[1;31m'
GREEN='\033[1;32m'
CYAN='\033[1;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Terminal Animation: Retro Typing Effect
type_out() {
    text="$1"
    color="$2"
    echo -ne "${color}"
    for ((i=0; i<${#text}; i++)); do
        echo -n "${text:$i:1}"
        sleep 0.03
    done
    echo -e "${NC}"
}

# Terminal Animation: Loading Spinner
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

clear
type_out "Initiating Emergency Override on $SYSTEM_NAME..." "$CYAN"
sleep 1

# 1. Audit the Rogue Daemon
echo -n "[+] [1/3] Auditing network for $APT_GROUP backdoor daemons... "
# Checks if ANY dockerd process is listening on the insecure 2375 port
if netstat -tulpn 2>/dev/null | grep -q ":2375"; then
    echo -e "${RED}FAILED${NC}"
    type_out "[-] ERROR: Rogue daemon still detected on port 2375!" "$RED"
    type_out "[-] Action Required: Locate the rogue process and terminate it before proceeding." "$YELLOW"
    exit 1
else
    echo -e "${GREEN}SECURED${NC}"
fi

sleep 1

# 2. Audit the C2 Web Dashboard
echo -n "[+] [2/3] Verifying internal C2 Web Dashboard status... "
# Checks if the web container is responding (assuming it's fixed and running on 8080)
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health | grep -q "200"; then
    echo -e "${GREEN}ONLINE${NC}"
else
    echo -e "${RED}FAILED${NC}"
    type_out "[-] ERROR: C2 Web Dashboard is unreachable." "$RED"
    type_out "[-] Action Required: Repair the container's Docker socket mount and restart the web service." "$YELLOW"
    exit 1
fi

sleep 1

# 3. Deadlock Injection Sequence (Animation)
type_out "[+] [3/3] System defenses verified. Compiling deadlock payload..." "$CYAN"

# Fake background process to trigger the spinner animation
(sleep 3) & 
spinner $!

type_out "[!] Injecting payload into Missile Guidance State Machine..." "$YELLOW"
(sleep 2) &
spinner $!

# The Payoff
echo ""
type_out "=======================================================" "$RED"
type_out " CRITICAL: STATE MACHINE FORCED INTO PERMANENT DEADLOCK" "$RED"
type_out " $APT_GROUP LAUNCH SEQUENCE SUCCESSFULLY ABORTED." "$RED"
type_out "=======================================================" "$RED"
echo ""
type_out "System locked. Code recovered:" "$GREEN"
echo "[+] Override accepted. Node secured."
echo "FLAG: $(cat /opt/c2/flag.txt)"
echo ""
