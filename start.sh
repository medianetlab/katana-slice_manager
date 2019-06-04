#!/bin/bash

# Start the docker containers on the background
docker-compose -f katana-mngr/docker-compose.yaml up -d
docker container run -d -it --net=host --name katana-cli-container --mount type=bind,src=$(pwd)/katana-cli/cli,dst=/katana-cli/cli katana-cli