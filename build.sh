#!/bin/bash

# *** Install development environment ***
# Check if the --dev option is given
if [[ "$1" == "--dev" ]];
then
    echo "Installing development environment"
    # Copy hard links of the shared utils in katana-mngr and katana-nbi
    read -r -p "Any development/dev_shared_utils will be lost. Continue? (Y/n) > " ans
    if [[ $ans =~ ^n.* ]];
    then
    exit 9999
    fi
    rm -rf katana-nbi/katana/shared_utils
    rm -rf development/dev_shared_utils
    cp -al katana-mngr/katana/shared_utils development/dev_shared_utils
    cp -al katana-mngr/katana/shared_utils katana-nbi/katana/

    # Create the dev folder if it is not there
    echo "Creating development/dev_config_files. They can be used for actual testing. They won't be pushed to remote repository"
    cp -r example_config_files/* development/dev_config_files/

fi

# Check if the user and release fare defined
while [[ $# -gt 0 ]]
do
    key=$1

    case $key in
    -r | --release)
        TAG_NUMBER=$2
        shift
        shift
    ;;
    -u | --user)
        DOCKER_USER=$2
        shift
        shift
    ;;
    esac
done

# Check if the tag number is set
if [ -z "${TAG_NUMBER+x}" ]; then
export TAG_NUMBER="test"
fi

# Check if the DOCKER_USER is set
if [ -z "${DOCKER_USER+x}" ]; then
export DOCKER_USER="mnlab"
fi

# Build the images
echo "**** Building the images ****"
docker image build -f katana-nbi/Dockerfile -t "${DOCKER_USER}"/katana-nbi:${TAG_NUMBER} .
docker image build -f katana-mngr/Dockerfile -t "${DOCKER_USER}"/katana-mngr:${TAG_NUMBER} .
docker image build -f katana-cli/Dockerfile -t "${DOCKER_USER}"/katana-cli:${TAG_NUMBER} .
docker image build -f katana-swagger/Dockerfile -t "${DOCKER_USER}"/katana-swagger:${TAG_NUMBER} .
docker image build -f katana-prometheus/Dockerfile -t "${DOCKER_USER}"/katana-prometheus:${TAG_NUMBER} .
docker image build -f katana-grafana/Dockerfile -t "${DOCKER_USER}"/katana-grafana:${TAG_NUMBER} .
docker image build -f katana-nfv_mon/Dockerfile -t "${DOCKER_USER}"/katana-nfv_mon:${TAG_NUMBER} .

# Tag the latest images
docker image tag "${DOCKER_USER}"/katana-nbi:${TAG_NUMBER} "${DOCKER_USER}"/katana-nbi:latest
docker image tag "${DOCKER_USER}"/katana-mngr:${TAG_NUMBER} "${DOCKER_USER}"/katana-mngr:latest
docker image tag "${DOCKER_USER}"/katana-cli:${TAG_NUMBER} "${DOCKER_USER}"/katana-cli:latest
docker image tag "${DOCKER_USER}"/katana-swagger:${TAG_NUMBER} "${DOCKER_USER}"/katana-swagger:latest
docker image tag "${DOCKER_USER}"/katana-prometheus:${TAG_NUMBER} "${DOCKER_USER}"/katana-prometheus:latest
docker image tag "${DOCKER_USER}"/katana-grafana:${TAG_NUMBER} "${DOCKER_USER}"/katana-grafana:latest
docker image tag "${DOCKER_USER}"/katana-nfv_mon:${TAG_NUMBER} "${DOCKER_USER}"/katana-nfv_mon:latest