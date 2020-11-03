#!/bin/bash

# Check if the tag number is set
if [ -z "${TAG_NUMBER+x}" ]; then
export TAG_NUMBER="test"
fi

# Get the service that needs to be built
SERVICE=$1
if [ -z "${SERVICE}" ]; then
echo "Error: The service to be built is not defined - Usage: service_build.sh <SERVICE_NAME>" 1>&2
exit 1
fi

# Build the images
echo "**** Building the images ****"
docker image build -f  "${SERVICE}"/Dockerfile -t mnlab/"${SERVICE}":${TAG_NUMBER} .

# Tag the latest images
docker image tag mnlab/"${SERVICE}":${TAG_NUMBER} mnlab/"${SERVICE}":latest
