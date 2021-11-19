#!/bin/bash

# Check for help option
if [[ " $* " =~ " -h " ]] || [[ " $* " =~ " --help " ]];
then
    printf "Usage:\n\tstop.sh [-c | --clear] [-h | --help]\nOptions:
\t[-c | --clear] : Remove the container volumes
\t[-h | --help] : Print this message and quit\n"
    exit 0
fi
 
# Get the options
while [[ $# -gt 0 ]]
do
    key=$1
    case $key in
    -c | --clear)
        options="$options -v"
        shift
        ;;
    *)
        printf "Wrong option %s\n--------\n" "${key}"
        printf "Usage:\n\tstop.sh [-c | --clear] [-h | --help]\nOptions:
\t[-c | --clear] : Remove the container volumes
\t[-h | --help] : Print this message and quit\n"
        exit 0
        ;;
    esac
done

# Get the project directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && cd .. && pwd )"

# Avoid warning messages
export DOCKER_TAG=""
export DOCKER_REG=""
export DOCKER_REG_USER=""
export DOCKER_REG_PASSWD=""
export DOCKER_REPO=""

# Stop the containers
docker-compose -f ${DIR}/docker-compose.yaml down ${options}

# Remove the katana-log files
rm -f katana-nbi/katana.log* katana-mngr/katana.log*
