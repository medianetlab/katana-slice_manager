#!/bin/bash

# Stop the containers
docker-compose -f katana-mngr/docker-compose.yaml down
docker container stop katana-cli-container

# Remove every docker container and image from the system
docker container rm katana-cli-container

# Remove the katana-container-log file
file=katana-container-logs
if [[ -L "$file" ]]; then
    rm -f $file
fi

# Remove the katana-log file
file=katana-mngr/katana.log*
    rm -f $file
 