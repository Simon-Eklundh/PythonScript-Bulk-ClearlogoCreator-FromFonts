#!/bin/sh
# Runs the logo creator once on container start, then once per night
# at RUN_TIME (HH:MM, default 03:00).

RUN_TIME="${RUN_TIME:-03:00}"

trap 'exit 0' TERM INT

while true; do
    python clearlogo_creator.py

    now=$(date +%s)
    next=$(date -d "$RUN_TIME" +%s)
    if [ "$next" -le "$now" ]; then
        next=$(date -d "tomorrow $RUN_TIME" +%s)
    fi

    echo "Next run at $(date -d "@$next")"
    sleep $(( next - now )) &
    wait $!
done
