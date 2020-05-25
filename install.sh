#!/bin/bash

# *** Install development environment ***
# Check if the --dev option is given
if [[ "$1" == "--dev" ]];
then
    echo "Installing development environment"
    # Copy hard links of the shared utils in katana-mngr and katana-nbi
    read -p "Any dev_shared_utils will be lost. Continue? (Y/n) > " ans
    if [[ $ans =~ ^n.* ]];
    then
    exit 9999
    fi
    rm -rf katana-nbi/katana/shared_utils
    rm -rf dev_shared_utils
    cp -al katana-mngr/katana/shared_utils dev_shared_utils
    cp -al katana-mngr/katana/shared_utils katana-nbi/katana/

    # Create the dev folder if it is not there
    if [ ! -d "dev" ];
    then
        mkdir -p dev/config_files
        cp -r example_config_files/* dev/config_files/
        echo "Created dev folder"
    fi
fi

# Install the command for the cli tool to /usr/local/bin/
command -v katana &> /dev/null || cp katana /usr/local/bin/

# Build the images
docker-compose -f docker-compose.yaml build
