#!/bin/bash

# Start the docker containers on the background

docker-compose -f docker-compose.yaml up -d mongo zookeeper kafka katana-mngr katana-cli swagger