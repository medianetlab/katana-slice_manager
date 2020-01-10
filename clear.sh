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

# Remove Kafka data
echo "Warning: Need root permission for removing Kafka and Zookeeper files"
rm -rf zk-kafka/*
