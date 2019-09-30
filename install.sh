#!/bin/bash

# Install the command for the cli tool to /usr/local/bin/
command -v katana || mv katana /usr/local/bin/

# Build the images
docker-compose -f docker-compose-ui.yaml build
# docker build -t katana-cli -f katana-cli/Dockerfile katana-cli/