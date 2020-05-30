#!/bin/bash

# Uninstall katana processes

# Stop all the containers and remove the db
./stop.sh

# Remove the docker images
docker image rm katana-mngr
docker image rm katana-nbi
docker image rm katana-ui
docker image rm katana-cli
docker image rm swaggerapi/swagger-ui
docker image rm python:3.7.4-slim
docker image rm mongo:4.0.5
docker image rm confluentinc/cp-zookeeper:5.3.2
docker image rm confluentinc/cp-enterprise-kafka:5.3.2
docker image prune -y

# Remove katana commands
rm /usr/local/bin/katana
