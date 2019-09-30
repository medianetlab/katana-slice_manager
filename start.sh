#!/bin/bash

# Start the docker containers on the background

docker-compose -f docker-compose.yaml up -d mongo katana-mngr katana-cli