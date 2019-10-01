#!/bin/bash

# Stop the containers
docker-compose down --volumes

# Remove the katana-container-log file
file=katana-container-logs
if [[ -L "$file" ]]; then
    rm -f $file
fi

# Remove the katana-log file
file=katana-mngr/katana.log*
    rm -f $file
 