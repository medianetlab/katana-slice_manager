#!/bin/bash

# Stop the containers
docker-compose -f katana-mngr/docker-compose.yaml down
docker container stop katana-cli-container

# Remove every docker container and image from the system
docker container rm katana-cli-container