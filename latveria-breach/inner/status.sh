#!/bin/bash
GOLD="\033[38;5;178m"
GREEN="\033[38;5;35m"
RED="\033[1;31m"
RESET="\033[0m"

if [ -f /tmp/.disarmed ]; then
    echo -e "${GREEN}[ LATVERIAN DEFENSE GRID ]${RESET}"
    echo "STATUS: DISARMED"
    exit 0
fi

if [ ! -f /tmp/.destruct_end ]; then
    echo -e "${GOLD}[ LATVERIAN DEFENSE GRID ]${RESET}"
    echo "STATUS: STANDBY (not armed)"
    exit 0
fi

END=$(cat /tmp/.destruct_end 2>/dev/null)
NOW=$(date +%s)
REMAINING=$(( END - NOW ))

if [ "$REMAINING" -le 0 ]; then
    echo -e "${RED}[ LATVERIAN DEFENSE GRID ]${RESET}"
    echo "STATUS: TIME EXPIRED"
    exit 0
fi

MIN=$(( REMAINING / 60 ))
SEC=$(( REMAINING % 60 ))
printf "${RED}[ LATVERIAN DEFENSE GRID ]${RESET}\n"
printf "STATUS: ARMED\n"
printf "TIME REMAINING: %02d:%02d\n" "$MIN" "$SEC"
