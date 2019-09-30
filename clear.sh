#!/bin/bash

# Stop the containers
docker-compose -f docker-compose-ui.yaml down
docker volume rm slicemanager_mongo-configdb slicemanager_mongo-datadb slicemanager_postgres