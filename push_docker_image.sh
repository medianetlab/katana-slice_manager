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
    *)
    printf "Wrong option %s\n--------\n" "${key}"
    exit 9999
    ;;
    esac
done

# Read the user and password if they are not given as options
if [ -z "${DOCKER_PASSWORD+x}" ] || [ -z "${DOCKER_USER+x}" ]; then
read -r -p "Enter the Docker hub user" DOCKER_USER 
read -r -p -s "Enter the password " DOCKER_PASSWORD
fi

docker login -u "${DOCKER_USER}" -p "${DOCKER_PASSWORD}"

# Push to the remote Docker Hub

if [ -z "${TAG_RELEASE+x}" ]; then
docker image push "${DOCKER_USER}"/katana-nbi:"${TAG_NUMBER}"
docker image push "${DOCKER_USER}"/katana-mngr:"${TAG_NUMBER}"
docker image push "${DOCKER_USER}"/katana-cli:"${TAG_NUMBER}"
docker image push "${DOCKER_USER}"/katana-swagger:"${TAG_NUMBER}"
docker image push "${DOCKER_USER}"/katana-prometheus:"${TAG_NUMBER}"
docker image push "${DOCKER_USER}"/katana-grafana:"${TAG_NUMBER}"
docker image push "${DOCKER_USER}"/katana-nfv_mon:"${TAG_NUMBER}"
fi

docker image push "${DOCKER_USER}"/katana-nbi:latest
docker image push "${DOCKER_USER}"/katana-mngr:latest
docker image push "${DOCKER_USER}"/katana-cli:latest
docker image push "${DOCKER_USER}"/katana-swagger:latest
docker image push "${DOCKER_USER}"/katana-prometheus:latest
docker image push "${DOCKER_USER}"/katana-grafana:latest
docker image push "${DOCKER_USER}"/katana-nfv_mon:latest
