#!/bin/bash

# Install the command for the cli tool to /usr/local/bin/
mv katana /usr/local/bin/

# Build the images
docker-compose -f katana-mngr/docker-compose.yaml build
docker build -t katana-cli -f katana-cli/Dockerfile katana-cli/