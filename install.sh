#!/bin/bash

# Install the command for the cli tool to /usr/local/bin/
command -v katana || cp katana /usr/local/bin/

# Build the images
docker-compose -f docker-compose.yaml build
