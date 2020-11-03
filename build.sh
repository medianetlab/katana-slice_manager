#!/bin/bash

# Check if the tag number is set
if [ -z "${TAG_NUMBER+x}" ]; then
export TAG_NUMBER="test"
fi

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

# Install the command for the cli tool to /usr/local/bin/
command -v katana &> /dev/null || cp katana /usr/local/bin/

# Build the images
echo "**** Building the images ****"
docker image build -f  katana-nbi/Dockerfile -t mnlab/katana-nbi:${TAG_NUMBER} .
docker image build -f  katana-mngr/Dockerfile -t mnlab/katana-mngr:${TAG_NUMBER} .
docker image build -f  katana-cli/Dockerfile -t mnlab/katana-cli:${TAG_NUMBER} .
docker image build -f  katana-swagger/Dockerfile -t mnlab/katana-swagger:${TAG_NUMBER} .
docker image build -f  katana-prometheus/Dockerfile -t mnlab/katana-prometheus:${TAG_NUMBER} .
docker image build -f  katana-grafana/Dockerfile -t mnlab/katana-grafana:${TAG_NUMBER} .
docker image build -f  katana-nfv_mon/Dockerfile -t mnlab/katana-nfv_mon:${TAG_NUMBER} .

# Tag the latest images
docker image tag mnlab/katana-nbi:${TAG_NUMBER} mnlab/katana-nbi:latest
docker image tag mnlab/katana-mngr:${TAG_NUMBER} mnlab/katana-mngr:latest
docker image tag mnlab/katana-cli:${TAG_NUMBER} mnlab/katana-cli:latest
docker image tag mnlab/katana-swagger:${TAG_NUMBER} mnlab/katana-swagger:latest
docker image tag mnlab/katana-prometheus:${TAG_NUMBER} mnlab/katana-prometheus:latest
docker image tag mnlab/katana-grafana:${TAG_NUMBER} mnlab/katana-grafana:latest
docker image tag mnlab/katana-nfv_mon:${TAG_NUMBER} mnlab/katana-nfv_mon:latest