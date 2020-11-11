#!/bin/bash

# Uninstall katana processes

# Stop all the containers and remove the db
./stop.sh -c &> /dev/null

# Remove the docker images
docker rmi -f $(docker images | grep katana | awk '{print $3}') &> /dev/null

# Remove katana commands
rm /usr/local/bin/katana || true
