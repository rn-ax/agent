#!/usr/bin/env bash
# Poll macOS Ethernet hardware ports for link-up transitions and announce them
# with a sound + spoken alert. Built for mapping ethernet wall jacks to
# numbered patch-panel/cabinet ports: run this on the MacBook left plugged
# into a wall jack, then plug a second MacBook into cabinet ports one at a
# time — this script chimes the instant the correct port completes the link.
#
# Usage:
#   ./link-watch.sh            # watch every Ethernet-labeled hardware port
#   ./link-watch.sh en6        # watch only the given device
set -euo pipefail

if [ $# -ge 1 ]; then
  devices="$1"
else
  devices=$(networksetup -listallhardwareports | awk '
    /^Hardware Port: .*Ethernet/ { getline; print $2 }
  ')
fi

if [ -z "$devices" ]; then
  echo "No Ethernet hardware ports found (pass a device name explicitly, e.g. en6)." >&2
  exit 1
fi

echo "Watching: $devices" >&2

# Indexed (not associative) arrays — macOS ships bash 3.2, which has no -A.
device_list=($devices)
last_status=()
for d in "${device_list[@]}"; do
  last_status+=("$(ifconfig "$d" 2>/dev/null | awk '/status:/ {print $2}' || true)")
done

while true; do
  sleep 0.5
  for i in "${!device_list[@]}"; do
    d="${device_list[$i]}"
    status=$(ifconfig "$d" 2>/dev/null | awk '/status:/ {print $2}' || true)
    if [ "$status" != "${last_status[$i]}" ]; then
      ts=$(date '+%H:%M:%S')
      if [ "$status" = "active" ]; then
        echo "$ts  $d: LINK UP"
        afplay /System/Library/Sounds/Glass.aiff >/dev/null 2>&1 &
        say "link up on $d" >/dev/null 2>&1 &
      else
        echo "$ts  $d: link down"
      fi
      last_status[$i]="$status"
    fi
  done
done
