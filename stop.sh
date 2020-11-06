#!/bin/bash

# Check for help option
if [[ " $* " =~ " -h " ]] || [[ " $* " =~ " --help " ]];
then
    printf "Usage:\n\tstart.sh [-c | --clear] [-h | --help]\nOptions:
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
    printf "Usage:\n\tstart.sh [-c | --clear] [-h | --help]\nOptions:
    \t[-c | --clear] : Remove the container volumes
    \t[-h | --help] : Print this message and quit\n"
    exit 0
    ;;
    esac
done

export KATANA_VERSION=""

# Stop the containers
docker-compose down ${options}

# Remove the monitoring variable
sed -i 's/KATANA_MONITORING=.*/KATANA_MONITORING=/' katana-mngr/.env

# Remove the katana-log files
rm -f katana-nbi/katana.log* katana-mngr/katana.log*
