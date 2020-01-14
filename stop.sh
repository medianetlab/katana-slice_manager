#!/bin/bash

# Stop the containers
docker-compose -f docker-compose.yaml down

# Remove the katana-container-log file
file=katana-container-logs
if [[ -L "$file" ]]; then
    rm -f $file
fi

# Remove the katana-log files
file1=katana-nbi/katana.log*
file2=katana-mngr/katana.log*
rm -f $file1 $file2
