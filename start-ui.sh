#!/bin/bash

# Start the docker containers on the background

docker-compose -f docker-compose.yaml up -d
docker exec -it katana-ui ui db init
docker exec -it katana-ui ui db seed