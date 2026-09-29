#!/bin/bash
GOLD="\033[38;5;178m"
RESET="\033[0m"

echo -e "${GOLD}[ INTERCEPTED TECHNICIAN NOTES ]${RESET}"
echo ""
echo "- Check what you're allowed to run as root without a password."
echo "- If a spawned root shell keeps reappearing every time you type"
echo "  'exit', it's not stuck - the tool you're using is re-triggering"
echo "  itself once per matching file. Most GTFOBins-style 'find' payloads"
echo "  support a flag that stops it after the first match."
echo "- Once you're root, look for something that isn't meant to be there."
echo "- ./status shows the grid countdown at any time."
