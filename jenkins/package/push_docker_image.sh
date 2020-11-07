#!/bin/bash

# Push docker images to docker hub

# *** Docker Login ***
# Check the options to see if user and password are defined
while [[ $# -gt 0 ]]
do
    key=$1

    case $key in
    -p | --password)
        DOCKER_PASSWORD=$2
        shift
        shift
    ;;
    -u | --user)
        DOCKER_USER=$2
        shift
        shift
    ;;
    -r | --release)
        TAG_NUMBER=$2
        shift
        shift
    ;;
    -s | --service)
        SERVICE=$2
        shift
        shift
    ;;
    *)
    printf "Wrong option %s\n--------\n" "${key}"
    exit 9999
    ;;
    esac
done

docker login -u "${DOCKER_USER}" -p "${DOCKER_PASSWORD}"

# Push to the remote Docker Hub

docker image push "${DOCKER_USER}"/"${SERVICE}":"${TAG_NUMBER}"

docker image push "${DOCKER_USER}"/"${SERVICE}":latest