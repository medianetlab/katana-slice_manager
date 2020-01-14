#!/bin/bash

# Stop the containers
docker-compose -f docker-compose.yaml down

# Remove the katana-container-log file
file=katana-container-logs
if [[ -L "$file" ]]; then
    rm -f $file
fi

# Remove the katana-log file
file=katana-nbi/katana.log*
    rm -f $file
 