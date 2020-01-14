#!/bin/bash

# Install the command for the cli tool to /usr/local/bin/
command -v katana || cp katana /usr/local/bin/

# Move the shared utils into the container folders
cp -r shared_utils/* katana-mngr/katana/utils/
cp -r shared_utils/* katana-nbi/katana/utils/

# Build the images
docker-compose -f docker-compose.yaml build
