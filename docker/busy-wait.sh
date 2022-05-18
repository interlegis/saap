#!/usr/bin/env bash

while true; do
    COUNT_PG=`psql $1 -c '\l \q' | grep saap | wc -l`
    if ! [ "$COUNT_PG" -eq "0" ]; then
       break
    fi
    echo "Waiting database setup..."
    sleep 10
done
